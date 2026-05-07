// W3-v2 의료적 디스클레이머 카피 — `docs/copy/medical-disclaimer-ko.md` 와 동일.
// 모든 진단 결과 카드 (이미지/오디오/병원) 는 본 모듈 텍스트 ID 를 import 해
// MedicalDisclaimer 컴포넌트 footer 에 표시 의무.

export type DisclaimerKey = 'IMAGE' | 'AUDIO' | 'HOSPITAL';

export const MEDICAL_DISCLAIMER_KO: Record<DisclaimerKey, readonly string[]> = {
  IMAGE: [
    '※ AI 추정 결과이며 진단이 아닙니다.',
    '※ 증상 의심 시 반드시 수의사 진료를 받으세요.',
    '※ 사진 1장만으로 진단을 확정할 수 없습니다.',
  ],
  AUDIO: [
    '※ AI 추정 결과이며 진단이 아닙니다.',
    '※ 호흡·기침이 의심스럽다면 즉시 수의사 진료를 받으세요.',
    '※ 5–10초 녹음만으로 호흡기 질환을 확정할 수 없습니다.',
  ],
  HOSPITAL: [
    '※ 영업/진료 시간은 변동될 수 있으니 방문 전 전화 확인을 권장합니다.',
    '※ 응급 상황이라면 24시 동물의료센터로 즉시 연락하세요.',
  ],
} as const;
