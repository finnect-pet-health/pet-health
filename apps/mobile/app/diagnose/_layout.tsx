import { Stack } from 'expo-router';

export default function DiagnoseLayout() {
  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Screen name="camera" />
      <Stack.Screen name="audio" />
    </Stack>
  );
}
