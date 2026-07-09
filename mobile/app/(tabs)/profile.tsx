import React, { useCallback, useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Alert,
  FlatList,
  ScrollView,
  Switch,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useFocusEffect, useRouter } from 'expo-router';
import * as ImagePicker from 'expo-image-picker';
import { useAuthStore } from '../../store/authStore';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { ChipSelect } from '../../components/ui/ChipSelect';
import { COLORS, TAXONOMY } from '../../constants/config';
import { THEME, utilityTitle, SHADOW } from '../../constants/theme';
import { useClosetStore } from '../../store/closetStore';
import { useRoutineStore } from '../../store/routineStore';
import { tripsAPI, notificationsAPI, emailIngestAPI, socialAPI, styleAPI } from '../../services/api';
import { getApiErrorMessage } from '../../services/errors';
import { getDeviceTimezone, registerPushWithBackend } from '../../services/pushNotifications';
import { EmailIngestLog, EmailIngestSettings, TripPlan, TripPackingPlan, hasPremiumAccess, StreakStats, StyleProfile } from '../../types';
import { StreakCard } from '../../components/StreakBadge';
import { StyleProfileCard } from '../../components/profile/StyleProfileCard';

export default function ProfileScreen() {
  const router = useRouter();
  const { user, logout } = useAuthStore();
  const { items, fetchItems } = useClosetStore();
  const { routine, fetchRoutine, saveRoutine, sendMyPlan, saving, loading } = useRoutineStore();

  const [tripPlans, setTripPlans] = useState<TripPlan[]>([]);
  const [packingPlan, setPackingPlan] = useState<TripPackingPlan | null>(null);
  const [packingLoading, setPackingLoading] = useState<number | null>(null);
  const [destination, setDestination] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [days, setDays] = useState('3');
  const [loadingTrips, setLoadingTrips] = useState(false);

  const [wakeTime, setWakeTime] = useState('07:00');
  const [weekdayActivities, setWeekdayActivities] = useState<string[]>(['work']);
  const [weekendActivities, setWeekendActivities] = useState<string[]>(['everyday']);
  const [gymDays, setGymDays] = useState<string[]>([]);
  const [defaultWeather, setDefaultWeather] = useState('');
  const [routineEnabled, setRoutineEnabled] = useState(true);
  const [notificationsEnabled, setNotificationsEnabled] = useState(false);
  const [testingPush, setTestingPush] = useState(false);
  const [emailIngest, setEmailIngest] = useState<EmailIngestSettings | null>(null);
  const [emailLogs, setEmailLogs] = useState<EmailIngestLog[]>([]);
  const [simulatingEmail, setSimulatingEmail] = useState(false);
  const [streak, setStreak] = useState<StreakStats | null>(null);
  const [styleProfile, setStyleProfile] = useState<StyleProfile | null>(null);
  const [styleProfileLoading, setStyleProfileLoading] = useState(false);
  const deviceTimezone = getDeviceTimezone();

  const loadStyleProfile = useCallback(async () => {
    setStyleProfileLoading(true);
    try {
      const profile = await styleAPI.getProfile();
      setStyleProfile(profile);
    } catch {
      setStyleProfile(null);
    } finally {
      setStyleProfileLoading(false);
    }
  }, []);

  const loadEmailIngest = useCallback(async () => {
    try {
      const [settings, logs] = await Promise.all([
        emailIngestAPI.getSettings(),
        emailIngestAPI.getLogs(),
      ]);
      setEmailIngest(settings);
      setEmailLogs(logs);
    } catch {
      setEmailIngest(null);
      setEmailLogs([]);
    }
  }, []);

  const loadTrips = useCallback(async () => {
    if (!hasPremiumAccess(user)) {
      setTripPlans([]);
      return;
    }
    setLoadingTrips(true);
    try {
      const plans = await tripsAPI.listPlans();
      setTripPlans(plans);
    } catch {
      setTripPlans([]);
    } finally {
      setLoadingTrips(false);
    }
  }, [user]);

  const loadPacking = async (planId: number) => {
    setPackingLoading(planId);
    try {
      const plan = await tripsAPI.getPacking(planId);
      setPackingPlan(plan);
    } catch (error: any) {
      Alert.alert('Packing failed', getApiErrorMessage(error, 'Could not build a packing list.'));
    } finally {
      setPackingLoading(null);
    }
  };

  const loadStreak = useCallback(async () => {
    try {
      const stats = await socialAPI.getStreak(deviceTimezone);
      setStreak(stats);
    } catch {
      setStreak(null);
    }
  }, [deviceTimezone]);

  useFocusEffect(
    useCallback(() => {
      loadTrips();
      fetchRoutine();
      loadEmailIngest();
      loadStreak();
      loadStyleProfile();
    }, [loadTrips, fetchRoutine, loadEmailIngest, loadStreak, loadStyleProfile]),
  );

  useEffect(() => {
    if (!routine) return;
    setWakeTime(routine.wake_time);
    setWeekdayActivities(routine.weekday_activities);
    setWeekendActivities(routine.weekend_activities);
    setGymDays(routine.gym_days);
    setDefaultWeather(routine.default_weather_tag || '');
    setRoutineEnabled(routine.enabled);
    setNotificationsEnabled(routine.notifications_enabled);
  }, [routine]);

  const toggleIn = (list: string[], value: string) =>
    list.includes(value) ? list.filter((v) => v !== value) : [...list, value];

  const handleSaveRoutine = async () => {
    try {
      await saveRoutine({
        wake_time: wakeTime.trim() || '07:00',
        weekday_activities: weekdayActivities.length ? weekdayActivities : ['work'],
        weekend_activities: weekendActivities.length ? weekendActivities : ['everyday'],
        gym_days: gymDays,
        default_weather_tag: defaultWeather || null,
        enabled: routineEnabled,
        notifications_enabled: notificationsEnabled,
        timezone: deviceTimezone,
      });
      if (notificationsEnabled) {
        try {
          await registerPushWithBackend();
        } catch (error: any) {
          Alert.alert(
            'Routine saved',
            error?.message ||
              'Push needs a dev build (not Expo Go). Run `npx eas build --profile development` in mobile/.',
          );
          return;
        }
      }
      Alert.alert('Saved', 'Your daily routine is updated.');
    } catch {
      Alert.alert('Error', 'Could not save your routine.');
    }
  };

  const handleTestNotification = async () => {
    setTestingPush(true);
    try {
      if (notificationsEnabled) {
        await registerPushWithBackend();
      }
      const result = await notificationsAPI.test();
      Alert.alert(result.title, result.body);
    } catch (error: any) {
      Alert.alert(
        'Test failed',
        error?.message || 'Register push in a dev build first, then try again.',
      );
    } finally {
      setTestingPush(false);
    }
  };

  const handleSendMyPlan = async () => {
    try {
      await sendMyPlan();
      router.push('/(tabs)/home');
    } catch {
      Alert.alert('Error', 'Could not build your plan. Add clean clothes to your closet first.');
    }
  };

  const handleLogout = () => {
    Alert.alert(
      'Log Out',
      'Are you sure you want to log out?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Log Out',
          style: 'destructive',
          onPress: async () => {
            await logout();
            router.replace('/(auth)/login');
          },
        },
      ],
    );
  };

  const createTripPlan = async () => {
    if (!destination.trim()) {
      Alert.alert('Invalid trip', 'Add a destination.');
      return;
    }

    const hasDates = startDate.trim() && endDate.trim();
    const parsedDays = Number(days);

    if (!hasDates && (Number.isNaN(parsedDays) || parsedDays < 1)) {
      Alert.alert('Invalid trip', 'Add start & end dates (YYYY-MM-DD) or a valid number of days.');
      return;
    }

    try {
      await tripsAPI.createPlan({
        destination: destination.trim(),
        ...(hasDates
          ? { start_date: startDate.trim(), end_date: endDate.trim() }
          : { days: parsedDays }),
      });
      setDestination('');
      setStartDate('');
      setEndDate('');
      setDays('3');
      setPackingPlan(null);
      await loadTrips();
    } catch (error: any) {
      Alert.alert('Trip failed', getApiErrorMessage(error, 'Could not create that trip.'));
    }
  };

  const handleSimulateEmailImport = async () => {
    const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permission.granted) {
      Alert.alert('Permission needed', 'Enable photo access to test email import.');
      return;
    }
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 0.7,
    });
    if (result.canceled || !result.assets?.length) return;

    const asset = result.assets[0];
    setSimulatingEmail(true);
    try {
      const importResult = await emailIngestAPI.simulate({
        uri: asset.uri,
        name: asset.fileName,
        mimeType: asset.mimeType,
      });
      await Promise.all([fetchItems(), loadEmailIngest()]);
      Alert.alert(
        'Import complete',
        `Added ${importResult.items_created} item(s) to your closet for review.`,
      );
    } catch (error: any) {
      Alert.alert('Import failed', getApiErrorMessage(error, 'Could not process that image.'));
    } finally {
      setSimulatingEmail(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>You</Text>
      </View>

      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>{user?.full_name.charAt(0).toUpperCase()}</Text>
        </View>

        <Text style={styles.name}>{user?.full_name}</Text>
        <Text style={styles.email}>{user?.email}</Text>
        <Text style={[styles.premiumBadge, hasPremiumAccess(user) ? styles.premiumOn : styles.premiumOff]}>
          {hasPremiumAccess(user) ? 'Premium trial active' : 'Free Plan'}
        </Text>

        <View style={styles.stats}>
          <View style={styles.statBox}>
            <Text style={styles.statNumber}>{items.length}</Text>
            <Text style={styles.statLabel}>Items</Text>
          </View>
          <View style={styles.statBox}>
            <Text style={styles.statNumber}>{streak?.total_fit_days ?? 0}</Text>
            <Text style={styles.statLabel}>Fit days</Text>
          </View>
          <View style={styles.statBox}>
            <Text style={styles.statNumber}>{streak?.current_streak ?? 0}</Text>
            <Text style={styles.statLabel}>Streak</Text>
          </View>
        </View>

        <View style={styles.streakSection}>
          <StreakCard streak={streak} />
        </View>

        <View style={styles.streakSection}>
          <StyleProfileCard profile={styleProfile} loading={styleProfileLoading} />
        </View>

        <View style={styles.emailCard}>
          <Text style={styles.cardTitle}>Email import</Text>
          <Text style={styles.cardHint}>{emailIngest?.instructions ?? 'Loading…'}</Text>
          {emailIngest?.enabled && emailIngest.address ? (
            <>
              <Text style={styles.emailLabel}>Your forwarding address</Text>
              <Text selectable style={styles.emailAddress}>
                {emailIngest.address}
              </Text>
              <Text style={styles.emailTip}>
                Forward order confirmations or receipt emails here. New items land in Closet with a
                Review badge.
              </Text>
            </>
          ) : null}
          {emailLogs.length > 0 ? (
            <View style={styles.emailLogs}>
              <Text style={styles.emailLabel}>Recent imports</Text>
              {emailLogs.slice(0, 3).map((log) => (
                <Text key={log.id} style={styles.emailLogItem}>
                  {log.items_created} item{log.items_created === 1 ? '' : 's'}
                  {log.subject ? ` · ${log.subject}` : ''}
                </Text>
              ))}
            </View>
          ) : null}
          <Button
            title="Test with receipt photo"
            variant="outline"
            loading={simulatingEmail}
            onPress={handleSimulateEmailImport}
            style={styles.sendPlanBtn}
          />
        </View>

        <View style={styles.routineCard}>
          <Text style={styles.cardTitle}>Daily routine</Text>
          <Text style={styles.cardHint}>
            Morning push uses your wake time in timezone {deviceTimezone}. Requires a dev build
            (not Expo Go) — free via EAS.
          </Text>

          <View style={styles.switchRow}>
            <Text style={styles.switchLabel}>Routine enabled</Text>
            <Switch value={routineEnabled} onValueChange={setRoutineEnabled} />
          </View>

          <Input
            label="Wake time (HH:MM)"
            value={wakeTime}
            onChangeText={setWakeTime}
            placeholder="07:00"
          />

          <ChipSelect
            label="Weekday activities"
            options={TAXONOMY.activities}
            selected={weekdayActivities}
            multiple
            onSelect={(v) => setWeekdayActivities((prev) => toggleIn(prev, v))}
          />
          <ChipSelect
            label="Weekend activities"
            options={TAXONOMY.activities}
            selected={weekendActivities}
            multiple
            onSelect={(v) => setWeekendActivities((prev) => toggleIn(prev, v))}
          />
          <ChipSelect
            label="Gym days (adds gym to plan)"
            options={TAXONOMY.weekdays}
            selected={gymDays}
            multiple
            onSelect={(v) => setGymDays((prev) => toggleIn(prev, v))}
          />
          <ChipSelect
            label="Default weather"
            options={TAXONOMY.weather}
            selected={defaultWeather}
            onSelect={(v) => setDefaultWeather((prev) => (prev === v ? '' : v))}
          />

          <View style={styles.switchRow}>
            <View style={styles.switchCopy}>
              <Text style={styles.switchLabel}>Morning notifications</Text>
              <Text style={styles.switchHint}>
                Push at wake time with today&apos;s outfit. Dev build required.
              </Text>
            </View>
            <Switch value={notificationsEnabled} onValueChange={setNotificationsEnabled} />
          </View>

          <Button title="Save routine" loading={saving} onPress={handleSaveRoutine} />
          <Button
            title="Send test notification"
            loading={testingPush}
            onPress={handleTestNotification}
            variant="outline"
            style={styles.sendPlanBtn}
          />
          <Button
            title="Send me my plan now"
            loading={loading}
            onPress={handleSendMyPlan}
            style={styles.sendPlanBtn}
          />
        </View>

        <View style={styles.tripCard}>
          <Text style={styles.cardTitle}>Trip Planner</Text>
          <Text style={styles.cardHint}>
            Add dates for a live weather forecast — we dress you per day (hot, rainy, etc.).
          </Text>
          {hasPremiumAccess(user) ? (
            <>
              <Input label="Destination" value={destination} onChangeText={setDestination} placeholder="Honolulu, Hawaii" />
              <Input
                label="Start date"
                value={startDate}
                onChangeText={setStartDate}
                placeholder="2026-07-24"
                autoCapitalize="none"
              />
              <Input
                label="End date"
                value={endDate}
                onChangeText={setEndDate}
                placeholder="2026-07-26"
                autoCapitalize="none"
              />
              <Input
                label="Days (if no dates)"
                value={days}
                onChangeText={setDays}
                keyboardType="number-pad"
                placeholder="3"
              />
              <Button title="Create Trip Plan" onPress={createTripPlan} />
              <FlatList
                style={styles.tripList}
                data={tripPlans}
                keyExtractor={(item) => item.id.toString()}
                refreshing={loadingTrips}
                onRefresh={loadTrips}
                scrollEnabled={false}
                ListEmptyComponent={<Text style={styles.tripEmpty}>No trips yet</Text>}
                renderItem={({ item }) => (
                  <View style={styles.tripRow}>
                    <Text style={styles.tripItem}>
                      {item.destination}
                      {item.start_date && item.end_date
                        ? ` • ${item.start_date} → ${item.end_date}`
                        : ` • ${item.days} days`}
                    </Text>
                    <Button
                      title="What to pack"
                      onPress={() => loadPacking(item.id)}
                      loading={packingLoading === item.id}
                      style={styles.tripPackBtn}
                    />
                  </View>
                )}
              />
              {packingPlan ? (
                <View style={styles.packingBox}>
                  <Text style={styles.packingSummary}>{packingPlan.summary}</Text>
                  {packingPlan.weather_note ? (
                    <Text style={styles.weatherNote}>{packingPlan.weather_note}</Text>
                  ) : null}
                  {packingPlan.days.map((day) => (
                    <Text key={day.day} style={styles.packingDay}>
                      {day.title}
                      {day.weather_summary ? `\n${day.weather_summary}` : ''}
                      {day.rationale ? `\n${day.rationale}` : ''}
                    </Text>
                  ))}
                  <Text style={styles.packingListTitle}>Suitcase ({packingPlan.packing_list.length})</Text>
                  {packingPlan.packing_list.map((item) => (
                    <Text key={item.id} style={styles.packingItem}>
                      • {item.name || item.category}
                    </Text>
                  ))}
                </View>
              ) : null}
            </>
          ) : (
            <Text style={styles.tripLocked}>Upgrade to premium to unlock trip planning.</Text>
          )}
        </View>

        <Button title="Log Out" onPress={handleLogout} variant="outline" style={styles.logoutButton} />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: THEME.utility.background },
  header: { paddingHorizontal: 22, paddingTop: 12, paddingBottom: 16, borderBottomWidth: 1, borderBottomColor: THEME.utility.border },
  title: { ...utilityTitle(28), textAlign: 'left' },
  content: { alignItems: 'center', padding: 22, paddingBottom: 40 },
  avatar: {
    width: 90,
    height: 90,
    borderRadius: 45,
    backgroundColor: THEME.brand.ink,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  avatarText: { fontSize: 36, fontWeight: '800', color: '#fff' },
  name: { fontSize: 24, fontWeight: '700', color: THEME.utility.text, marginBottom: 4 },
  email: { fontSize: 14, color: THEME.utility.textMuted, marginBottom: 10 },
  premiumBadge: {
    fontSize: 12,
    fontWeight: '700',
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 12,
    marginBottom: 20,
    overflow: 'hidden',
  },
  premiumOn: { backgroundColor: '#FFF5E8', color: '#B66A00' },
  premiumOff: { backgroundColor: THEME.utility.surfaceMuted, color: THEME.utility.textMuted },
  stats: { flexDirection: 'row', gap: 12, marginBottom: 20, width: '100%' },
  streakSection: { width: '100%', marginBottom: 20 },
  statBox: {
    flex: 1,
    backgroundColor: THEME.utility.surfaceMuted,
    padding: 20,
    borderRadius: 14,
    alignItems: 'center',
  },
  statNumber: { fontSize: 28, fontWeight: '800', color: THEME.brand.ink, marginBottom: 4 },
  statLabel: { fontSize: 12, color: THEME.utility.textMuted },
  emailCard: {
    width: '100%',
    backgroundColor: THEME.editorial.surface,
    borderRadius: 16,
    padding: 16,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: THEME.editorial.border,
    ...SHADOW.soft,
  },
  emailLabel: { fontSize: 12, fontWeight: '700', color: COLORS.text, marginTop: 8, marginBottom: 4 },
  emailAddress: {
    fontSize: 14,
    color: COLORS.primary,
    fontWeight: '600',
    marginBottom: 8,
  },
  emailTip: { fontSize: 13, color: COLORS.textLight, marginBottom: 4 },
  emailLogs: { marginTop: 8, marginBottom: 8 },
  emailLogItem: { fontSize: 13, color: COLORS.text, paddingVertical: 4 },
  routineCard: {
    width: '100%',
    backgroundColor: THEME.editorial.surface,
    borderRadius: 16,
    padding: 16,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: THEME.editorial.border,
    ...SHADOW.soft,
  },
  cardTitle: { fontSize: 16, fontWeight: '700', color: COLORS.text, marginBottom: 6 },
  cardHint: { fontSize: 12, color: COLORS.textLight, lineHeight: 17, marginBottom: 12 },
  switchRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  switchCopy: { flex: 1, marginRight: 12 },
  switchLabel: { fontSize: 14, fontWeight: '600', color: COLORS.text },
  switchHint: { fontSize: 11, color: COLORS.textLight, marginTop: 2 },
  sendPlanBtn: { marginTop: 10 },
  logoutButton: { width: '100%', marginTop: 8 },
  tripCard: {
    width: '100%',
    backgroundColor: THEME.editorial.surface,
    borderRadius: 16,
    padding: 16,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: THEME.editorial.border,
    ...SHADOW.soft,
  },
  tripLocked: { fontSize: 13, color: COLORS.textLight },
  tripList: { maxHeight: 220, marginTop: 10 },
  tripRow: { marginBottom: 8 },
  tripItem: { fontSize: 13, color: COLORS.text, paddingVertical: 4 },
  tripPackBtn: { marginTop: 4 },
  packingBox: {
    marginTop: 12,
    padding: 14,
    backgroundColor: THEME.editorial.pill,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: THEME.editorial.border,
  },
  packingSummary: { fontSize: 14, fontWeight: '700', color: COLORS.text, marginBottom: 8 },
  weatherNote: { fontSize: 12, color: COLORS.warning, marginBottom: 8, lineHeight: 17 },
  packingDay: { fontSize: 12, color: COLORS.textLight, marginBottom: 8, lineHeight: 17 },
  packingListTitle: { fontSize: 13, fontWeight: '700', color: COLORS.text, marginTop: 10, marginBottom: 4 },
  packingItem: { fontSize: 12, color: COLORS.text, paddingVertical: 2 },
  tripEmpty: { fontSize: 13, color: COLORS.textLight, marginTop: 6 },
});
