// AC15 — 가까운 병원 화면.
// expo-location → /v1/hospitals/nearby → FlatList. KakaoMap WebView 통합은
// W1 spike 컴포넌트 + KAKAO_JS_API_KEY 셋업 후 별도 commit 으로.

import { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { searchHospitalsNearby } from '../../src/api/hospitals';
import type { HospitalNearbyList } from '../../src/api/types';
import { HospitalListItem } from '../../src/components/HospitalListItem';
import { MedicalDisclaimer } from '../../src/components/MedicalDisclaimer';
import { getCurrentLocation } from '../../src/permissions/location';

type LoadState =
  | { kind: 'idle' }
  | { kind: 'loading' }
  | { kind: 'denied' }
  | { kind: 'error'; message: string }
  | { kind: 'ready'; data: HospitalNearbyList };

const SEOUL_CITY_HALL = { lat: 37.5665, lng: 126.978 };

export default function HospitalsScreen() {
  const [state, setState] = useState<LoadState>({ kind: 'idle' });

  const load = useCallback(async () => {
    setState({ kind: 'loading' });
    const loc = await getCurrentLocation();
    const coords = loc.ok ? loc.coords : SEOUL_CITY_HALL; // dev fallback
    try {
      const data = await searchHospitalsNearby({
        lat: coords.lat,
        lng: coords.lng,
        radius_m: 3000,
        limit: 3,
      });
      if (!loc.ok && loc.reason === 'denied') {
        setState({ kind: 'denied' });
        return;
      }
      setState({ kind: 'ready', data });
    } catch (e) {
      setState({
        kind: 'error',
        message: e instanceof Error ? e.message : '병원 정보를 불러오지 못했어요.',
      });
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>가까운 동물병원</Text>
        <Text style={styles.subtitle}>현재 위치 기준 3km 이내 3곳</Text>
      </View>

      {state.kind === 'loading' || state.kind === 'idle' ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color="#3870e0" />
        </View>
      ) : null}

      {state.kind === 'denied' ? (
        <View style={styles.center}>
          <Text style={styles.message}>위치 권한이 필요합니다.</Text>
          <Pressable onPress={load} style={styles.retryButton}>
            <Text style={styles.retryText}>다시 시도</Text>
          </Pressable>
        </View>
      ) : null}

      {state.kind === 'error' ? (
        <View style={styles.center}>
          <Text style={styles.message}>{state.message}</Text>
          <Pressable onPress={load} style={styles.retryButton}>
            <Text style={styles.retryText}>다시 시도</Text>
          </Pressable>
        </View>
      ) : null}

      {state.kind === 'ready' ? (
        state.data.length === 0 ? (
          <View style={styles.center}>
            <Text style={styles.message}>주변 동물병원이 없습니다.</Text>
          </View>
        ) : (
          <FlatList
            data={state.data}
            keyExtractor={(item) => item.id}
            renderItem={({ item }) => (
              <HospitalListItem
                name={item.name}
                road_addr={item.road_addr}
                tel={item.tel}
                distance_m={item.distance_m}
              />
            )}
            ListFooterComponent={
              <View style={styles.footer}>
                <MedicalDisclaimer variant="HOSPITAL" />
              </View>
            }
          />
        )
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fafafa' },
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
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 24 },
  message: { fontSize: 14, color: '#555', textAlign: 'center', marginBottom: 12 },
  retryButton: {
    paddingVertical: 10,
    paddingHorizontal: 22,
    backgroundColor: '#3870e0',
    borderRadius: 8,
  },
  retryText: { color: '#fff', fontWeight: '600' },
  footer: { padding: 16 },
});
