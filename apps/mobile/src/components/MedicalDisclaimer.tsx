// 모든 진단/병원 결과 카드 footer 의무 컴포넌트. spec 02 § 7.

import { StyleSheet, Text, View } from 'react-native';
import {
  MEDICAL_DISCLAIMER_KO,
  type DisclaimerKey,
} from '../copy/medical-disclaimer-ko';

interface Props {
  variant: DisclaimerKey;
}

export function MedicalDisclaimer({ variant }: Props) {
  const lines = MEDICAL_DISCLAIMER_KO[variant];
  return (
    <View style={styles.box}>
      {lines.map((line, idx) => (
        <Text key={idx} style={styles.line}>
          {line}
        </Text>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  box: {
    marginTop: 12,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#eee',
  },
  line: {
    fontSize: 12,
    color: '#777',
    lineHeight: 18,
  },
});
