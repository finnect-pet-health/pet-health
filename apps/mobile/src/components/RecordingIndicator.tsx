// 5–10초 오디오 녹음 시각 게이지.

import { StyleSheet, Text, View } from 'react-native';

interface Props {
  /** 0..max */
  elapsedMs: number;
  /** 권장 max (= 10000ms) */
  maxMs: number;
  /** 권장 최소 (= 5000ms) — 이전엔 안내, 이후엔 정상 색 */
  minMs: number;
}

export function RecordingIndicator({ elapsedMs, maxMs, minMs }: Props) {
  const ratio = Math.min(1, elapsedMs / maxMs);
  const seconds = Math.floor(elapsedMs / 1000);
  const reachedMin = elapsedMs >= minMs;
  return (
    <View style={styles.container}>
      <View style={styles.barOuter}>
        <View
          style={[
            styles.barFill,
            { width: `${ratio * 100}%`, backgroundColor: reachedMin ? '#16a34a' : '#f59e0b' },
          ]}
        />
      </View>
      <View style={styles.legendRow}>
        <Text style={[styles.timer, reachedMin && styles.timerOk]}>{seconds}s</Text>
        <Text style={styles.hint}>
          {reachedMin ? '충분 — 종료 가능' : `최소 ${Math.ceil(minMs / 1000)}초 권장`}
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { width: '100%' },
  barOuter: {
    height: 10,
    backgroundColor: '#eef1f6',
    borderRadius: 5,
    overflow: 'hidden',
  },
  barFill: { height: '100%' },
  legendRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: 6,
  },
  timer: { fontSize: 18, fontWeight: '700', color: '#f59e0b', fontVariant: ['tabular-nums'] },
  timerOk: { color: '#16a34a' },
  hint: { fontSize: 12, color: '#777' },
});
