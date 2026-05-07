import { StyleSheet, Text, View } from 'react-native';
import { useAuthStore } from '../src/auth/store';

export default function Home() {
  const user = useAuthStore((s) => s.user);

  return (
    <View style={styles.container}>
      <Text style={styles.title}>PetFinect</Text>
      <Text style={styles.subtitle}>반려견 AI 헬스케어 + 의료비 예측·적금</Text>
      {user ? (
        <Text style={styles.welcome}>안녕하세요, {user.name}님!</Text>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 24,
    backgroundColor: '#fff',
  },
  title: { fontSize: 32, fontWeight: '700', marginBottom: 8 },
  subtitle: { fontSize: 16, color: '#555', marginBottom: 32, textAlign: 'center' },
  welcome: { fontSize: 16, color: '#333', fontWeight: '500' },
});
