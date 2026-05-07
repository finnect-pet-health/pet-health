import { useRouter } from 'expo-router';
import { useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { loginWithMock, MockUserCode } from '../src/api/auth';
import { useAuthStore } from '../src/auth/store';

const MOCK_USERS: { code: MockUserCode; label: string }[] = [
  { code: 'mock-user-1', label: 'Mock User 1' },
  { code: 'mock-user-2', label: 'Mock User 2' },
  { code: 'mock-user-3', label: 'Mock User 3' },
];

export default function LoginScreen() {
  const router = useRouter();
  const setSession = useAuthStore((s) => s.setSession);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleMockLogin = async (code: MockUserCode) => {
    setLoading(true);
    setError(null);
    try {
      const session = await loginWithMock(code);
      setSession(session);
      router.replace('/');
    } catch (e) {
      const message =
        e instanceof Error ? e.message : '로그인에 실패했습니다.';
      setError(message);
      Alert.alert('로그인 실패', message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>PetFinect 시작하기</Text>
        <Text style={styles.subtitle}>반려견 AI 헬스케어 + 의료비 예측·적금</Text>
      </View>

      {/* 카카오 로그인 버튼 (W2 합류 예정) */}
      <Pressable style={[styles.kakaoButton, styles.kakaoDisabled]} disabled>
        <View style={styles.kakaoInner}>
          {/* 카카오 로고 대체 텍스트 */}
          <Text style={styles.kakaoLogo}>K</Text>
          <Text style={styles.kakaoText}>카카오로 시작하기</Text>
        </View>
      </Pressable>
      <Text style={styles.kakaoNote}>
        실 카카오 OAuth는 W2 합류 예정
      </Text>

      {/* 개발 모드 섹션 — __DEV__ 일 때만 노출 */}
      {__DEV__ && (
        <View style={styles.devSection}>
          <View style={styles.devDivider}>
            <View style={styles.dividerLine} />
            <Text style={styles.devLabel}>개발 모드</Text>
            <View style={styles.dividerLine} />
          </View>

          {error ? <Text style={styles.errorText}>{error}</Text> : null}

          {MOCK_USERS.map(({ code, label }) => (
            <Pressable
              key={code}
              style={({ pressed }) => [
                styles.mockButton,
                pressed && styles.mockButtonPressed,
                loading && styles.mockButtonDisabled,
              ]}
              onPress={() => handleMockLogin(code)}
              disabled={loading}
            >
              {loading ? (
                <ActivityIndicator size="small" color="#555" />
              ) : (
                <Text style={styles.mockButtonText}>{label}로 로그인</Text>
              )}
            </Pressable>
          ))}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
    paddingHorizontal: 24,
    paddingTop: 80,
    alignItems: 'center',
  },
  header: {
    alignItems: 'center',
    marginBottom: 48,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: '#111',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 14,
    color: '#777',
    textAlign: 'center',
  },
  kakaoButton: {
    width: '100%',
    backgroundColor: '#FEE500',
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: 'center',
  },
  kakaoDisabled: {
    opacity: 0.5,
  },
  kakaoInner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  kakaoLogo: {
    fontSize: 18,
    fontWeight: '900',
    color: '#3A1D1D',
  },
  kakaoText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#3A1D1D',
  },
  kakaoNote: {
    marginTop: 8,
    fontSize: 12,
    color: '#aaa',
  },
  devSection: {
    width: '100%',
    marginTop: 40,
  },
  devDivider: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: '#e0e0e0',
  },
  devLabel: {
    marginHorizontal: 12,
    fontSize: 12,
    color: '#999',
    fontWeight: '600',
  },
  errorText: {
    color: '#d32f2f',
    fontSize: 13,
    textAlign: 'center',
    marginBottom: 12,
  },
  mockButton: {
    backgroundColor: '#f5f5f5',
    borderRadius: 10,
    paddingVertical: 13,
    alignItems: 'center',
    marginBottom: 10,
    borderWidth: 1,
    borderColor: '#e0e0e0',
    minHeight: 46,
    justifyContent: 'center',
  },
  mockButtonPressed: {
    backgroundColor: '#ebebeb',
  },
  mockButtonDisabled: {
    opacity: 0.6,
  },
  mockButtonText: {
    fontSize: 15,
    color: '#333',
    fontWeight: '500',
  },
});
