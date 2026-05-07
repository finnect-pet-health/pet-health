// 이미지/오디오 진단 결과 공용 카드.
// AC13/14: top_results + action 칩 + confidence 바 + 의료적 디스클레이머 푸터.

import { StyleSheet, Text, View } from 'react-native';
import type { DisclaimerKey } from '../copy/medical-disclaimer-ko';
import { MedicalDisclaimer } from './MedicalDisclaimer';

interface TopResult {
  label?: string;
  category?: string;
  score: number;
}

interface Props {
  modality: 'image' | 'audio';
  top_results: TopResult[];
  action: string;
  confidence_top1: number;
}

const ACTION_TOKEN: Record<string, { color: string; text: string; label: string }> = {
  immediate: { color: '#d32f2f', text: '#fff', label: '즉시 진료' },
  schedule: { color: '#f59e0b', text: '#fff', label: '진료 예약' },
  observe: { color: '#3870e0', text: '#fff', label: '관찰' },
};

function pct(score: number): string {
  return `${Math.round(score * 100)}%`;
}

export function DiagnosisResultCard({
  modality,
  top_results,
  action,
  confidence_top1,
}: Props) {
  const variant: DisclaimerKey = modality === 'image' ? 'IMAGE' : 'AUDIO';
  const tok = ACTION_TOKEN[action] ?? ACTION_TOKEN.observe;
  return (
    <View style={styles.card}>
      <View style={styles.headerRow}>
        <Text style={styles.title}>
          {modality === 'image' ? '이미지 분석 결과' : '오디오 분석 결과'}
        </Text>
        <View style={[styles.chip, { backgroundColor: tok.color }]}>
          <Text style={[styles.chipText, { color: tok.text }]}>{tok.label}</Text>
        </View>
      </View>

      <View style={styles.confidence}>
        <Text style={styles.confidenceLabel}>최고 신뢰도</Text>
        <View style={styles.bar}>
          <View
            style={[styles.barFill, { width: `${Math.round(confidence_top1 * 100)}%` }]}
          />
        </View>
        <Text style={styles.confidenceValue}>{pct(confidence_top1)}</Text>
      </View>

      <View style={styles.topList}>
        {top_results.map((r, idx) => {
          const name = r.label ?? r.category ?? '결과';
          return (
            <View key={`${name}-${idx}`} style={styles.topRow}>
              <Text style={styles.topName} numberOfLines={1}>
                {idx + 1}. {name}
              </Text>
              <Text style={styles.topScore}>{pct(r.score)}</Text>
            </View>
          );
        })}
      </View>

      <MedicalDisclaimer variant={variant} />
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    margin: 16,
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowRadius: 4,
    shadowOffset: { width: 0, height: 1 },
    elevation: 1,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  title: { fontSize: 16, fontWeight: '700', color: '#111' },
  chip: { paddingVertical: 4, paddingHorizontal: 10, borderRadius: 12 },
  chipText: { fontSize: 12, fontWeight: '700' },
  confidence: { marginBottom: 12 },
  confidenceLabel: { fontSize: 12, color: '#777', marginBottom: 6 },
  bar: { height: 8, backgroundColor: '#eef1f6', borderRadius: 4, overflow: 'hidden' },
  barFill: { height: '100%', backgroundColor: '#3870e0' },
  confidenceValue: { marginTop: 4, fontSize: 13, color: '#3870e0', fontWeight: '600', textAlign: 'right' },
  topList: { gap: 6 },
  topRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  topName: { fontSize: 14, color: '#222', flex: 1, marginRight: 8 },
  topScore: { fontSize: 13, color: '#555', fontVariant: ['tabular-nums'] },
});
