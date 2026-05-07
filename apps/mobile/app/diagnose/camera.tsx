// AC13 — 카메라 진단 화면.
// 4부위 선택 → expo-camera 촬영 → uploadAndDiagnoseImage → DiagnosisResultCard.

import { CameraView } from 'expo-camera';
import { useLocalSearchParams } from 'expo-router';
import { useEffect, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { uploadAndDiagnoseImage, type ImageRegion } from '../../src/api/diagnose';
import { readFileAsBytes } from '../../src/api/file';
import type { DiagnosisOut } from '../../src/api/types';
import { DiagnosisResultCard } from '../../src/components/DiagnosisResultCard';
import { ensureCameraPermission } from '../../src/permissions/camera';

const REGIONS: { key: ImageRegion; label: string }[] = [
  { key: 'skin', label: '피부' },
  { key: 'eye', label: '눈' },
  { key: 'ear', label: '귀' },
  { key: 'gum', label: '잇몸' },
];

type Phase =
  | { kind: 'pick-region' }
  | { kind: 'permission-denied' }
  | { kind: 'camera'; region: ImageRegion }
  | { kind: 'uploading'; region: ImageRegion }
  | { kind: 'result'; region: ImageRegion; result: DiagnosisOut }
  | { kind: 'error'; message: string };

export default function CameraScreen() {
  const { pet_id } = useLocalSearchParams<{ pet_id?: string }>();
  const [phase, setPhase] = useState<Phase>({ kind: 'pick-region' });
  const cameraRef = useRef<CameraView>(null);

  const onPickRegion = async (region: ImageRegion) => {
    const perm = await ensureCameraPermission();
    if (!perm.ok) {
      setPhase({ kind: 'permission-denied' });
      return;
    }
    setPhase({ kind: 'camera', region });
  };

  const onCapture = async () => {
    if (phase.kind !== 'camera' || !cameraRef.current) return;
    const region = phase.region;

    if (!pet_id) {
      Alert.alert('오류', '펫 정보가 없습니다. 다시 시도해주세요.');
      return;
    }

    setPhase({ kind: 'uploading', region });
    try {
      const photo = await cameraRef.current.takePictureAsync({
        quality: 0.7,
        skipProcessing: false,
      });
      if (!photo) throw new Error('사진 촬영에 실패했습니다.');

      const result = await uploadAndDiagnoseImage({
        petId: pet_id,
        region,
        fileUri: photo.uri,
        contentType: 'image/jpeg',
        loadBody: readFileAsBytes,
      });
      setPhase({ kind: 'result', region, result });
    } catch (e) {
      setPhase({
        kind: 'error',
        message: e instanceof Error ? e.message : '진단에 실패했습니다.',
      });
    }
  };

  useEffect(() => {
    if (!pet_id) {
      setPhase({ kind: 'error', message: '펫 ID 없이 카메라 화면에 접근했습니다.' });
    }
  }, [pet_id]);

  if (phase.kind === 'pick-region') {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.title}>이미지 진단</Text>
          <Text style={styles.subtitle}>촬영할 부위를 선택하세요</Text>
        </View>
        <View style={styles.regionGrid}>
          {REGIONS.map((r) => (
            <Pressable
              key={r.key}
              style={({ pressed }) => [
                styles.regionButton,
                pressed && styles.regionPressed,
              ]}
              onPress={() => onPickRegion(r.key)}
            >
              <Text style={styles.regionLabel}>{r.label}</Text>
            </Pressable>
          ))}
        </View>
      </View>
    );
  }

  if (phase.kind === 'permission-denied') {
    return (
      <View style={[styles.container, styles.center]}>
        <Text style={styles.message}>카메라 권한이 필요합니다.</Text>
        <Pressable
          style={styles.retry}
          onPress={() => setPhase({ kind: 'pick-region' })}
        >
          <Text style={styles.retryText}>다시 선택</Text>
        </Pressable>
      </View>
    );
  }

  if (phase.kind === 'camera') {
    return (
      <View style={styles.cameraWrap}>
        <CameraView ref={cameraRef} style={StyleSheet.absoluteFill} facing="back" />
        <View style={styles.cameraOverlay}>
          <Text style={styles.cameraHint}>{regionLabel(phase.region)} 부위 촬영</Text>
          <Pressable onPress={onCapture} style={styles.shutter}>
            <View style={styles.shutterInner} />
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
          <Text style={styles.title}>{regionLabel(phase.region)} 진단 결과</Text>
        </View>
        <DiagnosisResultCard
          modality="image"
          top_results={phase.result.top_results as { label: string; score: number }[]}
          action={phase.result.action}
          confidence_top1={phase.result.confidence_top1}
        />
        <Pressable
          style={styles.retry}
          onPress={() => setPhase({ kind: 'pick-region' })}
        >
          <Text style={styles.retryText}>다시 촬영</Text>
        </Pressable>
      </ScrollView>
    );
  }

  return (
    <View style={[styles.container, styles.center]}>
      <Text style={styles.message}>{phase.message}</Text>
      <Pressable
        style={styles.retry}
        onPress={() => setPhase({ kind: 'pick-region' })}
      >
        <Text style={styles.retryText}>다시 시도</Text>
      </Pressable>
    </View>
  );
}

function regionLabel(r: ImageRegion): string {
  return REGIONS.find((x) => x.key === r)?.label ?? r;
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
  regionGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    padding: 20,
    gap: 12,
  },
  regionButton: {
    width: '48%',
    aspectRatio: 1.5,
    borderRadius: 12,
    backgroundColor: '#fff',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  regionPressed: { backgroundColor: '#eef1f6' },
  regionLabel: { fontSize: 18, fontWeight: '600', color: '#222' },
  cameraWrap: { flex: 1, backgroundColor: '#000' },
  cameraOverlay: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    paddingBottom: 48,
    alignItems: 'center',
  },
  cameraHint: {
    color: '#fff',
    fontSize: 14,
    marginBottom: 16,
    backgroundColor: 'rgba(0,0,0,0.4)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
  },
  shutter: {
    width: 76,
    height: 76,
    borderRadius: 38,
    borderWidth: 4,
    borderColor: '#fff',
    alignItems: 'center',
    justifyContent: 'center',
  },
  shutterInner: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: '#fff',
  },
  message: { fontSize: 14, color: '#555', textAlign: 'center', marginVertical: 12 },
  retry: {
    margin: 20,
    paddingVertical: 12,
    backgroundColor: '#3870e0',
    borderRadius: 8,
    alignItems: 'center',
  },
  retryText: { color: '#fff', fontWeight: '600', fontSize: 15 },
});
