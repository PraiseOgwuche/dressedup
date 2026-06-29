import { useEffect, useState } from 'react';
import { ActivityIndicator, View } from 'react-native';
import { Stack, useRouter } from 'expo-router';
import * as Notifications from 'expo-notifications';
import { useAuthStore } from '../store/authStore';
import { useRoutineStore } from '../store/routineStore';
import { COLORS } from '../constants/config';

export default function RootLayout() {
  const router = useRouter();
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const loadUser = useAuthStore((state) => state.loadUser);
  const fetchRoutine = useRoutineStore((state) => state.fetchRoutine);
  const syncPushIfEnabled = useRoutineStore((state) => state.syncPushIfEnabled);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    loadUser().finally(() => setIsReady(true));
  }, []);

  useEffect(() => {
    if (!isAuthenticated) return;
    fetchRoutine().then(() => syncPushIfEnabled());
  }, [isAuthenticated, fetchRoutine, syncPushIfEnabled]);

  useEffect(() => {
    const sub = Notifications.addNotificationResponseReceivedListener(() => {
      router.push('/(tabs)/home');
    });
    return () => sub.remove();
  }, [router]);

  if (!isReady) {
    return (
      <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
        <ActivityIndicator size="large" color={COLORS.primary} />
      </View>
    );
  }

  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Protected guard={!isAuthenticated}>
        <Stack.Screen name="(auth)" />
      </Stack.Protected>
      <Stack.Protected guard={isAuthenticated}>
        <Stack.Screen name="(tabs)" />
      </Stack.Protected>
    </Stack>
  );
}
