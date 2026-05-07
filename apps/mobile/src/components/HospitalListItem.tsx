// 가까운 병원 리스트 단일 row. 전화 tap → tel: 링크, 거리 m/km 자동 포맷.

import { Linking, Pressable, StyleSheet, Text, View } from 'react-native';

interface Props {
  name: string;
  road_addr: string;
  tel: string;
  distance_m: number;
}

function formatDistance(m: number): string {
  if (m < 1000) return `${Math.round(m)}m`;
  return `${(m / 1000).toFixed(1)}km`;
}

function formatTel(tel: string): string {
  return tel.replace(/[^0-9+]/g, '');
}

export function HospitalListItem({ name, road_addr, tel, distance_m }: Props) {
  const handleCall = () => {
    if (!tel) return;
    void Linking.openURL(`tel:${formatTel(tel)}`);
  };

  return (
    <View style={styles.row}>
      <View style={styles.headRow}>
        <Text style={styles.name} numberOfLines={1}>
          {name}
        </Text>
        <Text style={styles.distance}>{formatDistance(distance_m)}</Text>
      </View>
      {road_addr ? (
        <Text style={styles.addr} numberOfLines={2}>
          {road_addr}
        </Text>
      ) : null}
      {tel ? (
        <Pressable
          onPress={handleCall}
          style={({ pressed }) => [
            styles.telButton,
            pressed && styles.telButtonPressed,
          ]}
        >
          <Text style={styles.telLabel}>전화</Text>
          <Text style={styles.telNumber}>{tel}</Text>
        </Pressable>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
    backgroundColor: '#fff',
  },
  headRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  name: {
    flex: 1,
    fontSize: 15,
    fontWeight: '600',
    color: '#111',
    marginRight: 8,
  },
  distance: {
    fontSize: 13,
    color: '#3870e0',
    fontWeight: '500',
  },
  addr: {
    fontSize: 13,
    color: '#555',
    marginBottom: 8,
  },
  telButton: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    paddingVertical: 6,
    paddingHorizontal: 10,
    backgroundColor: '#f1f5fb',
    borderRadius: 8,
    gap: 6,
  },
  telButtonPressed: {
    backgroundColor: '#e1ebf7',
  },
  telLabel: {
    fontSize: 12,
    color: '#3870e0',
    fontWeight: '600',
  },
  telNumber: {
    fontSize: 13,
    color: '#1a4ec2',
  },
});
