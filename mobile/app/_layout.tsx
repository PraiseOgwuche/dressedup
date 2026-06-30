import { useCallback, useEffect, useState } from 'react';
import { Stack, useRouter } from 'expo-router';
import * as Notifications from 'expo-notifications';
import * as SplashScreen from 'expo-splash-screen';

import { useAuthStore } from '../store/authStore';
import { useRoutineStore } from '../store/routineStore';
import { BrandSplash } from '../components/BrandSplash';

// Keep native cream splash visible until BrandSplash mounts and hides it.
SplashScreen.preventAutoHideAsync().catch(() => {});

export default function RootLayout() {
  const router = useRouter();
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const loadUser = useAuthStore((state) => state.loadUser);
  const fetchRoutine = useRoutineStore((state) => state.fetchRoutine);
  const syncPushIfEnabled = useRoutineStore((state) => state.syncPushIfEnabled);
  const [authReady, setAuthReady] = useState(false);
  const [splashDone, setSplashDone] = useState(false);

  useEffect(() => {
    loadUser().finally(() => setAuthReady(true));
  }, [loadUser]);

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

  const finishSplash = useCallback(() => setSplashDone(true), []);

  if (!splashDone) {
    return <BrandSplash authReady={authReady} onFinish={finishSplash} />;
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
