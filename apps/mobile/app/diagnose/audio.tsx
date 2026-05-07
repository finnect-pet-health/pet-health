// AC14 — 오디오 진단 화면.
// 카운트다운 3-2-1 → expo-av 5–10초 녹음 → uploadAndDiagnoseAudio → 결과 카드.

import { Audio } from 'expo-av';
import { useLocalSearchParams } from 'expo-router';
import { useCallback, useEffect, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { uploadAndDiagnoseAudio } from '../../src/api/diagnose';
import { readFileAsBytes } from '../../src/api/file';
import type { DiagnosisOut } from '../../src/api/types';
import { DiagnosisResultCard } from '../../src/components/DiagnosisResultCard';
import { RecordingIndicator } from '../../src/components/RecordingIndicator';
import { ensureAudioPermission } from '../../src/permissions/audio';

const COUNTDOWN_SEC = 3;
const MIN_RECORD_MS = 5000;
const MAX_RECORD_MS = 10000;

type Phase =
  | { kind: 'idle' }
  | { kind: 'permission-denied' }
  | { kind: 'countdown'; remaining: number }
  | { kind: 'recording'; elapsedMs: number }
  | { kind: 'uploading' }
  | { kind: 'result'; result: DiagnosisOut }
  | { kind: 'error'; message: string };

export default function AudioScreen() {
  const { pet_id } = useLocalSearchParams<{ pet_id?: string }>();
  const [phase, setPhase] = useState<Phase>({ kind: 'idle' });
  const recordingRef = useRef<Audio.Recording | null>(null);
  const elapsedTickRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const countdownTickRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const startTsRef = useRef<number>(0);

  useEffect(() => {
    return () => {
      if (elapsedTickRef.current) clearInterval(elapsedTickRef.current);
      if (countdownTickRef.current) clearInterval(countdownTickRef.current);
      if (recordingRef.current) {
        void recordingRef.current.stopAndUnloadAsync().catch(() => undefined);
      }
    };
  }, []);

  const stopRecording = useCallback(async () => {
    if (!recordingRef.current) return null;
    if (elapsedTickRef.current) clearInterval(elapsedTickRef.current);
    elapsedTickRef.current = null;
    try {
      await recordingRef.current.stopAndUnloadAsync();
    } catch {
      // already stopped
    }
    const uri = recordingRef.current.getURI();
    recordingRef.current = null;
    return uri;
  }, []);

  const finishUpload = useCallback(
    async (uri: string) => {
      if (!pet_id) {
        setPhase({ kind: 'error', message: '펫 ID 없이 오디오 화면에 접근했습니다.' });
        return;
      }
      setPhase({ kind: 'uploading' });
      try {
        const result = await uploadAndDiagnoseAudio({
          petId: pet_id,
          fileUri: uri,
          contentType: 'audio/m4a',
          loadBody: readFileAsBytes,
        });
        setPhase({ kind: 'result', result });
      } catch (e) {
        setPhase({
          kind: 'error',
          message: e instanceof Error ? e.message : '진단에 실패했습니다.',
        });
      }
    },
    [pet_id],
  );

  const startRecording = useCallback(async () => {
    try {
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
      });
      const recording = new Audio.Recording();
      await recording.prepareToRecordAsync(
        Audio.RecordingOptionsPresets.HIGH_QUALITY,
      );
      await recording.startAsync();
      recordingRef.current = recording;
      startTsRef.current = Date.now();
      setPhase({ kind: 'recording', elapsedMs: 0 });

      elapsedTickRef.current = setInterval(() => {
        const elapsed = Date.now() - startTsRef.current;
        if (elapsed >= MAX_RECORD_MS) {
          // auto-stop
          void (async () => {
            const uri = await stopRecording();
            if (uri) await finishUpload(uri);
          })();
          return;
        }
        setPhase({ kind: 'recording', elapsedMs: elapsed });
      }, 100);
    } catch (e) {
      setPhase({
        kind: 'error',
        message: e instanceof Error ? e.message : '녹음 시작에 실패했습니다.',
      });
    }
  }, [finishUpload, stopRecording]);

  const onStart = async () => {
    const perm = await ensureAudioPermission();
    if (!perm.ok) {
      setPhase({ kind: 'permission-denied' });
      return;
    }
    if (!pet_id) {
      Alert.alert('오류', '펫 정보가 없습니다.');
      return;
    }

    setPhase({ kind: 'countdown', remaining: COUNTDOWN_SEC });
    let remaining = COUNTDOWN_SEC;
    countdownTickRef.current = setInterval(() => {
      remaining -= 1;
      if (remaining <= 0) {
        if (countdownTickRef.current) clearInterval(countdownTickRef.current);
        countdownTickRef.current = null;
        void startRecording();
        return;
      }
      setPhase({ kind: 'countdown', remaining });
    }, 1000);
  };

  const onStop = async () => {
    const uri = await stopRecording();
    if (!uri) return;
    if (Date.now() - startTsRef.current < MIN_RECORD_MS) {
      Alert.alert('너무 짧습니다', `최소 ${MIN_RECORD_MS / 1000}초 이상 녹음해주세요.`);
      setPhase({ kind: 'idle' });
      return;
    }
    await finishUpload(uri);
  };

  if (phase.kind === 'idle') {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.title}>오디오 진단</Text>
          <Text style={styles.subtitle}>5–10초간 녹음해 호흡/기침을 분석합니다</Text>
        </View>
        <View style={styles.body}>
          <Text style={styles.guide}>
            반려동물 입 근처에서 5~10초간{'\n'}녹음해주세요.
          </Text>
          <Pressable
            style={({ pressed }) => [styles.recordButton, pressed && styles.recordPressed]}
            onPress={onStart}
          >
            <Text style={styles.recordText}>녹음 시작</Text>
          </Pressable>
        </View>
      </View>
    );
  }

  if (phase.kind === 'permission-denied') {
    return (
      <View style={[styles.container, styles.center]}>
        <Text style={styles.message}>마이크 권한이 필요합니다.</Text>
        <Pressable style={styles.retry} onPress={() => setPhase({ kind: 'idle' })}>
          <Text style={styles.retryText}>다시 시도</Text>
        </Pressable>
      </View>
    );
  }

  if (phase.kind === 'countdown') {
    return (
      <View style={[styles.container, styles.center]}>
        <Text style={styles.countdown}>{phase.remaining}</Text>
        <Text style={styles.message}>곧 녹음을 시작합니다.</Text>
      </View>
    );
  }

  if (phase.kind === 'recording') {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.title}>녹음 중…</Text>
        </View>
        <View style={styles.body}>
          <RecordingIndicator
            elapsedMs={phase.elapsedMs}
            minMs={MIN_RECORD_MS}
            maxMs={MAX_RECORD_MS}
          />
          <Pressable style={styles.stopButton} onPress={onStop}>
            <Text style={styles.stopText}>중지 + 분석</Text>
          </Pressable>
        </View>
      </View>
    );
  }

  if (phase.kind === 'uploading') {
    return (
      <View style={[styles.container, styles.center]}>
        <ActivityIndicator size="large" color="#3870e0" />
        <Text style={styles.message}>분석 중…</Text>
      </View>
    );
  }

  if (phase.kind === 'result') {
    return (
      <ScrollView style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.title}>오디오 진단 결과</Text>
        </View>
        <DiagnosisResultCard
          modality="audio"
          top_results={phase.result.top_results as { category: string; score: number }[]}
          action={phase.result.action}
          confidence_top1={phase.result.confidence_top1}
        />
        <Pressable style={styles.retry} onPress={() => setPhase({ kind: 'idle' })}>
          <Text style={styles.retryText}>다시 녹음</Text>
        </Pressable>
      </ScrollView>
    );
  }

  return (
    <View style={[styles.container, styles.center]}>
      <Text style={styles.message}>{phase.message}</Text>
      <Pressable style={styles.retry} onPress={() => setPhase({ kind: 'idle' })}>
        <Text style={styles.retryText}>다시 시도</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fafafa' },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 24 },
  header: {
    paddingHorizontal: 20,
    paddingTop: 60,
    paddingBottom: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  title: { fontSize: 22, fontWeight: '700', color: '#111' },
  subtitle: { marginTop: 4, fontSize: 13, color: '#777' },
  body: { padding: 24, gap: 24 },
  guide: { fontSize: 14, color: '#444', textAlign: 'center', lineHeight: 22 },
  recordButton: {
    backgroundColor: '#d32f2f',
    paddingVertical: 18,
    borderRadius: 12,
    alignItems: 'center',
  },
  recordPressed: { backgroundColor: '#b91c1c' },
  recordText: { color: '#fff', fontSize: 17, fontWeight: '700' },
  countdown: { fontSize: 88, fontWeight: '800', color: '#3870e0' },
  message: { fontSize: 14, color: '#555', textAlign: 'center', marginVertical: 12 },
  stopButton: {
    backgroundColor: '#111',
    paddingVertical: 14,
    borderRadius: 10,
    alignItems: 'center',
    marginTop: 12,
  },
  stopText: { color: '#fff', fontSize: 15, fontWeight: '600' },
  retry: {
    margin: 20,
    paddingVertical: 12,
    backgroundColor: '#3870e0',
    borderRadius: 8,
    alignItems: 'center',
  },
  retryText: { color: '#fff', fontWeight: '600', fontSize: 15 },
});
