import { useRouter } from 'expo-router';
import { useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Modal,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { families as familiesApi } from '../../src/api/families';
import { useAuthStore } from '../../src/auth/store';

type ActiveModal = 'create' | 'join' | null;

export default function FamilyOnboardingScreen() {
  const router = useRouter();
  const setFamilies = useAuthStore((s) => s.setFamilies);

  const [activeModal, setActiveModal] = useState<ActiveModal>(null);
  const [familyName, setFamilyName] = useState('');
  const [inviteCode, setInviteCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const resetModal = () => {
    setActiveModal(null);
    setFamilyName('');
    setInviteCode('');
    setError(null);
    setLoading(false);
  };

  const handleCreate = async () => {
    const trimmed = familyName.trim();
    if (!trimmed) {
      setError('가족 이름을 입력해 주세요.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await familiesApi.create(trimmed);
      const updated = await familiesApi.list();
      setFamilies(updated);
      resetModal();
      router.replace('/');
    } catch (e) {
      const message =
        e instanceof Error ? e.message : '가족 생성에 실패했습니다.';
      setError(message);
      Alert.alert('오류', message);
    } finally {
      setLoading(false);
    }
  };

  const handleJoin = async () => {
    const trimmed = inviteCode.trim();
    if (!trimmed) {
      setError('초대 코드를 입력해 주세요.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await familiesApi.join(trimmed);
      const updated = await familiesApi.list();
      setFamilies(updated);
      resetModal();
      router.replace('/');
    } catch (e) {
      const message =
        e instanceof Error ? e.message : '가족 참여에 실패했습니다.';
      setError(message);
      Alert.alert('오류', message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>가족 설정</Text>
      <Text style={styles.subtitle}>
        반려견을 함께 케어할 가족을 만들거나{'\n'}초대 코드로 기존 가족에 참여하세요.
      </Text>

      <Pressable
        style={({ pressed }) => [styles.primaryButton, pressed && styles.buttonPressed]}
        onPress={() => setActiveModal('create')}
      >
        <Text style={styles.primaryButtonText}>가족 만들기</Text>
      </Pressable>

      <Pressable
        style={({ pressed }) => [styles.secondaryButton, pressed && styles.buttonPressed]}
        onPress={() => setActiveModal('join')}
      >
        <Text style={styles.secondaryButtonText}>초대 코드로 참여</Text>
      </Pressable>

      {/* 가족 만들기 모달 */}
      <Modal
        visible={activeModal === 'create'}
        transparent
        animationType="fade"
        onRequestClose={resetModal}
      >
        <View style={styles.overlay}>
          <View style={styles.modalCard}>
            <Text style={styles.modalTitle}>가족 만들기</Text>
            <Text style={styles.modalLabel}>가족 이름</Text>
            <TextInput
              style={styles.input}
              placeholder="예: 보리네"
              placeholderTextColor="#bbb"
              value={familyName}
              onChangeText={setFamilyName}
              autoFocus
              maxLength={30}
              returnKeyType="done"
              onSubmitEditing={handleCreate}
            />
            {error ? <Text style={styles.errorText}>{error}</Text> : null}
            <View style={styles.modalActions}>
              <Pressable
                style={[styles.modalBtn, styles.cancelBtn]}
                onPress={resetModal}
                disabled={loading}
              >
                <Text style={styles.cancelBtnText}>취소</Text>
              </Pressable>
              <Pressable
                style={[styles.modalBtn, styles.confirmBtn, loading && styles.disabledBtn]}
                onPress={handleCreate}
                disabled={loading}
              >
                {loading ? (
                  <ActivityIndicator size="small" color="#fff" />
                ) : (
                  <Text style={styles.confirmBtnText}>만들기</Text>
                )}
              </Pressable>
            </View>
          </View>
        </View>
      </Modal>

      {/* 초대 코드로 참여 모달 */}
      <Modal
        visible={activeModal === 'join'}
        transparent
        animationType="fade"
        onRequestClose={resetModal}
      >
        <View style={styles.overlay}>
          <View style={styles.modalCard}>
            <Text style={styles.modalTitle}>초대 코드로 참여</Text>
            <Text style={styles.modalLabel}>초대 코드</Text>
            <TextInput
              style={styles.input}
              placeholder="8자리 코드 입력"
              placeholderTextColor="#bbb"
              value={inviteCode}
              onChangeText={setInviteCode}
              autoCapitalize="characters"
              autoFocus
              maxLength={8}
              returnKeyType="done"
              onSubmitEditing={handleJoin}
            />
            {error ? <Text style={styles.errorText}>{error}</Text> : null}
            <View style={styles.modalActions}>
              <Pressable
                style={[styles.modalBtn, styles.cancelBtn]}
                onPress={resetModal}
                disabled={loading}
              >
                <Text style={styles.cancelBtnText}>취소</Text>
              </Pressable>
              <Pressable
                style={[styles.modalBtn, styles.confirmBtn, loading && styles.disabledBtn]}
                onPress={handleJoin}
                disabled={loading}
              >
                {loading ? (
                  <ActivityIndicator size="small" color="#fff" />
                ) : (
                  <Text style={styles.confirmBtnText}>참여하기</Text>
                )}
              </Pressable>
            </View>
          </View>
        </View>
      </Modal>
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
  title: {
    fontSize: 26,
    fontWeight: '700',
    color: '#111',
    marginBottom: 12,
  },
  subtitle: {
    fontSize: 14,
    color: '#777',
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: 48,
  },
  primaryButton: {
    width: '100%',
    backgroundColor: '#111',
    borderRadius: 12,
    paddingVertical: 15,
    alignItems: 'center',
    marginBottom: 12,
  },
  primaryButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
  secondaryButton: {
    width: '100%',
    backgroundColor: '#fff',
    borderRadius: 12,
    paddingVertical: 15,
    alignItems: 'center',
    borderWidth: 1.5,
    borderColor: '#ddd',
  },
  secondaryButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  buttonPressed: {
    opacity: 0.75,
  },
  // ─── Modal ─────────────────────────────────────────────────────────
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.45)',
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 24,
  },
  modalCard: {
    width: '100%',
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 24,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111',
    marginBottom: 16,
  },
  modalLabel: {
    fontSize: 13,
    color: '#666',
    marginBottom: 6,
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 11,
    fontSize: 15,
    color: '#111',
    backgroundColor: '#fafafa',
    marginBottom: 8,
  },
  errorText: {
    color: '#d32f2f',
    fontSize: 12,
    marginBottom: 8,
  },
  modalActions: {
    flexDirection: 'row',
    marginTop: 8,
    gap: 10,
  },
  modalBtn: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 44,
  },
  cancelBtn: {
    backgroundColor: '#f0f0f0',
  },
  cancelBtnText: {
    fontSize: 15,
    color: '#555',
    fontWeight: '500',
  },
  confirmBtn: {
    backgroundColor: '#111',
  },
  confirmBtnText: {
    fontSize: 15,
    color: '#fff',
    fontWeight: '600',
  },
  disabledBtn: {
    opacity: 0.6,
  },
});
