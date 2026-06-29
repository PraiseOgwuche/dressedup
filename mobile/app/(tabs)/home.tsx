import React, { useCallback, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useFocusEffect, useRouter } from 'expo-router';
import { useAuthStore } from '../../store/authStore';
import { useRoutineStore } from '../../store/routineStore';
import { useClosetStore } from '../../store/closetStore';
import { COLORS, TAXONOMY } from '../../constants/config';
import { closetAPI, outfitAPI } from '../../services/api';
import { getApiErrorMessage } from '../../services/errors';
import { ClosetItem, OutfitSuggestion, DailyPlan, PlanActivity } from '../../types';
import { Button } from '../../components/ui/Button';
import { ChipSelect } from '../../components/ui/ChipSelect';
import { Input } from '../../components/ui/Input';
import { OutfitCard, OutfitSlotKey } from '../../components/OutfitCard';

export default function HomeScreen() {
  const router = useRouter();
  const { user } = useAuthStore();
  const { items, laundry, fetchItems, fetchLaundry } = useClosetStore();
  const [suggestion, setSuggestion] = useState<OutfitSuggestion | null>(null);
  const [occasion, setOccasion] = useState('');
  const [trend, setTrend] = useState('');
  const [weatherTag, setWeatherTag] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [wearing, setWearing] = useState(false);

  const [activities, setActivities] = useState<string[]>(['work']);
  const [plan, setPlan] = useState<DailyPlan | null>(null);
  const [planLoading, setPlanLoading] = useState(false);
  const [wearingActivity, setWearingActivity] = useState<string | null>(null);
  const [feedbackLoading, setFeedbackLoading] = useState(false);
  const [swappingSlot, setSwappingSlot] = useState<OutfitSlotKey | null>(null);
  const [askQuery, setAskQuery] = useState('');
  const [askLoading, setAskLoading] = useState(false);
  const [askInterpretation, setAskInterpretation] = useState<string | null>(null);
  const { sendMyPlan, consumePendingPlan, loading: routineLoading } = useRoutineStore();

  const outfitFeedbackPayload = (outfit: {
    top?: ClosetItem | null;
    bottom?: ClosetItem | null;
    shoes?: ClosetItem | null;
    outerwear?: ClosetItem | null;
  }) => ({
    top_id: outfit.top?.id ?? null,
    bottom_id: outfit.bottom?.id ?? null,
    shoes_id: outfit.shoes?.id ?? null,
    outerwear_id: outfit.outerwear?.id ?? null,
    occasion: occasion || null,
    weather_tag: weatherTag || null,
  });

  const sendOutfitFeedback = async (
    outfit: {
      top?: ClosetItem | null;
      bottom?: ClosetItem | null;
      shoes?: ClosetItem | null;
      outerwear?: ClosetItem | null;
    },
    signal: 'like' | 'dislike' | 'wore',
  ) => {
    if (!outfit.top && !outfit.bottom && !outfit.shoes) return;
    setFeedbackLoading(true);
    try {
      await outfitAPI.feedback({ ...outfitFeedbackPayload(outfit), signal });
      if (signal === 'dislike') {
        await loadSuggestion();
      }
    } catch {
      // Non-blocking — wear logging still succeeds if feedback fails.
    } finally {
      setFeedbackLoading(false);
    }
  };

  const loadSuggestion = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await outfitAPI.getSuggestion(
        occasion || undefined,
        weatherTag || undefined,
        undefined,
        trend || undefined,
      );
      setSuggestion(response);
    } catch {
      Alert.alert('Unable to load', 'Could not fetch outfit suggestions yet.');
    } finally {
      setIsLoading(false);
    }
  }, [occasion, weatherTag, trend]);

  const handleAsk = async () => {
    const query = askQuery.trim();
    if (query.length < 3) {
      Alert.alert('Say more', 'Try something like “Dress me for a cold work day, quiet luxury”.');
      return;
    }
    setAskLoading(true);
    try {
      const response = await outfitAPI.ask(query);
      setAskInterpretation(response.parsed.interpretation);
      setOccasion(response.parsed.occasion || '');
      setWeatherTag(response.parsed.weather_tag || '');
      setTrend(response.parsed.trend || '');
      setSuggestion(response.suggestion);
    } catch (error: any) {
      Alert.alert('Unable to dress you', getApiErrorMessage(error, 'Could not parse that request.'));
    } finally {
      setAskLoading(false);
    }
  };

  const loadPlan = useCallback(async () => {
    setPlanLoading(true);
    try {
      const response = await outfitAPI.plan(activities, weatherTag || undefined);
      setPlan(response);
    } catch {
      Alert.alert('Unable to plan', 'Could not build your day plan yet.');
    } finally {
      setPlanLoading(false);
    }
  }, [activities, weatherTag]);

  useFocusEffect(
    useCallback(() => {
      fetchItems();
      fetchLaundry();
      loadSuggestion();
      const pending = consumePendingPlan();
      if (pending) {
        setPlan(pending);
      } else {
        loadPlan();
      }
    }, [fetchItems, fetchLaundry, loadSuggestion, loadPlan, consumePendingPlan]),
  );

  const handleSendMyPlan = async () => {
    try {
      const response = await sendMyPlan();
      setPlan(response);
      const wear = response.activities.find((a) => a.mode === 'wear');
      const packCount = response.activities.filter((a) => a.mode === 'pack').length;
      let message = wear ? `Wear now: ${wear.title}` : 'Your plan is ready.';
      if (packCount) {
        message += `\n\nPack for ${packCount} more stop${packCount > 1 ? 's' : ''} today.`;
      }
      Alert.alert("Today's plan", message);
    } catch {
      Alert.alert('Unable to plan', 'Could not build a plan from your routine. Check Profile settings.');
    }
  };

  const wearItems = async (ids: number[]) => {
    await Promise.all(ids.map((id) => closetAPI.wear(id)));
    await Promise.all([loadSuggestion(), loadPlan()]);
  };

  const handleWoreSuggestion = async () => {
    const ids = [suggestion?.top, suggestion?.bottom, suggestion?.shoes, suggestion?.outerwear]
      .filter((i): i is ClosetItem => !!i)
      .map((i) => i.id);
    if (!ids.length) return;
    setWearing(true);
    try {
      await wearItems(ids);
      await sendOutfitFeedback(
        {
          top: suggestion?.top,
          bottom: suggestion?.bottom,
          shoes: suggestion?.shoes,
          outerwear: suggestion?.outerwear,
        },
        'wore',
      );
      Alert.alert('Logged', 'Marked as worn — anything past its wash limit is now in the hamper.');
    } catch (error: any) {
      Alert.alert('Error', getApiErrorMessage(error, 'Could not log this outfit.'));
    } finally {
      setWearing(false);
    }
  };

  const handleWoreActivity = async (activity: PlanActivity) => {
    const ids = [activity.top, activity.bottom, activity.shoes, activity.outerwear]
      .filter((i): i is ClosetItem => !!i)
      .map((i) => i.id);
    if (!ids.length) return;
    setWearingActivity(activity.activity);
    try {
      await wearItems(ids);
      await sendOutfitFeedback(
        {
          top: activity.top,
          bottom: activity.bottom,
          shoes: activity.shoes,
          outerwear: activity.outerwear,
        },
        'wore',
      );
      Alert.alert('Logged', `Marked your ${activity.title.toLowerCase()} outfit as worn.`);
    } catch (error: any) {
      Alert.alert('Error', getApiErrorMessage(error, 'Could not log this outfit.'));
    } finally {
      setWearingActivity(null);
    }
  };

  const handleSwapSlot = async (slot: OutfitSlotKey) => {
    if (!suggestion) return;
    setSwappingSlot(slot);
    try {
      const response = await outfitAPI.getSuggestion(
        occasion || undefined,
        weatherTag || undefined,
        {
          swapSlot: slot,
          topId: suggestion.top?.id,
          bottomId: suggestion.bottom?.id,
          shoesId: suggestion.shoes?.id,
          outerwearId: suggestion.outerwear?.id,
        },
        trend || undefined,
      );
      setSuggestion(response);
    } catch {
      Alert.alert('Unable to swap', 'No better alternative found in your closet for that piece.');
    } finally {
      setSwappingSlot(null);
    }
  };

  const toggleActivity = (value: string) => {
    setActivities((prev) =>
      prev.includes(value) ? prev.filter((a) => a !== value) : [...prev, value],
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView>
        <View style={styles.header}>
          <Text style={styles.title}>DressedUp</Text>
        </View>

        <View style={styles.content}>
          <Text style={styles.welcomeText}>Welcome, {user?.full_name}!</Text>

          {items.length === 0 ? (
            <View style={styles.emptyClosetCard}>
              <Text style={styles.emptyClosetTitle}>Closet is empty</Text>
              <Text style={styles.emptyClosetText}>
                Add a few items — try a flat-lay photo — and outfit plans will light up here.
              </Text>
              <Button title="Go to Closet" onPress={() => router.push('/(tabs)/closet')} />
            </View>
          ) : null}

          {laundry?.laundry_due ? (
            <View style={styles.laundryHint}>
              <Text style={styles.laundryHintText}>🧺 {laundry.message}</Text>
            </View>
          ) : null}

          <View style={styles.routineHero}>
            <Text style={styles.sectionTitle}>Ask DressedUp</Text>
            <Text style={styles.sectionHint}>
              Type what you need — we&apos;ll pick occasion, weather, and vibe for you.
            </Text>
            <Input
              placeholder="Dress me for a cold work day, quiet luxury…"
              value={askQuery}
              onChangeText={setAskQuery}
              onSubmitEditing={handleAsk}
              returnKeyType="go"
            />
            <Button title="Dress me" loading={askLoading} onPress={handleAsk} />
            {askInterpretation ? (
              <Text style={styles.askInterpretation}>{askInterpretation}</Text>
            ) : null}
          </View>

          <View style={styles.routineHero}>
            <Text style={styles.sectionTitle}>My routine</Text>
            <Text style={styles.sectionHint}>
              One tap — outfit from your saved routine (work, gym days, weather).
            </Text>
            <Button title="Send me my plan" loading={routineLoading} onPress={handleSendMyPlan} />
          </View>

          {/* Plan my day */}
          <View style={styles.planControls}>
            <Text style={styles.sectionTitle}>Plan my day</Text>
            <Text style={styles.sectionHint}>
              Pick what you&apos;re doing today. We&apos;ll dress you for the first thing and pack the rest.
            </Text>
            <ChipSelect
              label="Today I'm doing"
              options={TAXONOMY.activities}
              selected={activities}
              multiple
              onSelect={toggleActivity}
            />
            <ChipSelect
              label="Weather"
              options={TAXONOMY.weather}
              selected={weatherTag}
              onSelect={(v) => setWeatherTag((prev) => (prev === v ? '' : v))}
            />
            <Button title="Plan my day" loading={planLoading} onPress={loadPlan} />
          </View>

          {plan?.activities?.length ? (
            plan.activities.map((activity) => (
              <OutfitCard
                key={activity.activity}
                title={activity.title}
                badge={activity.mode === 'wear' ? 'WEAR NOW' : 'PACK'}
                rationale={activity.rationale}
                top={activity.top}
                bottom={activity.bottom}
                shoes={activity.shoes}
                outerwear={activity.outerwear}
                packingList={activity.mode === 'pack' ? activity.packing_list : undefined}
                onWore={activity.mode === 'wear' ? () => handleWoreActivity(activity) : undefined}
                woreLoading={wearingActivity === activity.activity}
              />
            ))
          ) : (
            <View style={styles.emptyPlan}>
              <Text style={styles.emptyPlanText}>
                Add some clean clothes to your closet, then tap “Plan my day”.
              </Text>
            </View>
          )}

          {/* Custom one-off outfit */}
          <View style={styles.divider} />
          <Text style={styles.sectionTitle}>Custom outfit</Text>
          <View style={styles.generatorCard}>
            <ChipSelect
              label="Occasion"
              options={TAXONOMY.occasions}
              selected={occasion}
              onSelect={(v) => setOccasion((prev) => (prev === v ? '' : v))}
            />
            <ChipSelect
              label="Vibe"
              options={TAXONOMY.trends}
              selected={trend}
              onSelect={(v) => setTrend((prev) => (prev === v ? '' : v))}
            />
            <Button title="Generate Outfit" loading={isLoading} onPress={loadSuggestion} />
          </View>

          <OutfitCard
            title={suggestion?.title || 'Daily outfit suggestion'}
            rationale={suggestion?.rationale}
            top={suggestion?.top}
            bottom={suggestion?.bottom}
            shoes={suggestion?.shoes}
            outerwear={suggestion?.outerwear}
            alternatives={suggestion?.alternatives}
            onLike={
              suggestion
                ? () =>
                    sendOutfitFeedback(
                      {
                        top: suggestion.top,
                        bottom: suggestion.bottom,
                        shoes: suggestion.shoes,
                        outerwear: suggestion.outerwear,
                      },
                      'like',
                    )
                : undefined
            }
            onDislike={
              suggestion
                ? () =>
                    sendOutfitFeedback(
                      {
                        top: suggestion.top,
                        bottom: suggestion.bottom,
                        shoes: suggestion.shoes,
                        outerwear: suggestion.outerwear,
                      },
                      'dislike',
                    )
                : undefined
            }
            feedbackLoading={feedbackLoading}
            onSwapSlot={suggestion ? handleSwapSlot : undefined}
            swappingSlot={swappingSlot}
            onWore={handleWoreSuggestion}
            woreLoading={wearing}
          />
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff' },
  header: { padding: 20, borderBottomWidth: 1, borderBottomColor: COLORS.border },
  title: { fontSize: 24, fontWeight: '800', color: COLORS.primary, textAlign: 'center' },
  content: { padding: 20 },
  welcomeText: { fontSize: 22, fontWeight: '700', marginBottom: 18, color: COLORS.text },
  emptyClosetCard: {
    backgroundColor: '#FFF8EE',
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#FFE0B2',
  },
  emptyClosetTitle: { fontSize: 17, fontWeight: '800', color: COLORS.text, marginBottom: 6 },
  emptyClosetText: { fontSize: 13, color: COLORS.textLight, lineHeight: 18, marginBottom: 12 },
  laundryHint: {
    backgroundColor: '#FFF3E0',
    borderRadius: 12,
    padding: 12,
    marginBottom: 16,
  },
  laundryHintText: { fontSize: 13, color: COLORS.warning, fontWeight: '600' },
  routineHero: {
    backgroundColor: '#EEF0FF',
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#D8DCFF',
  },
  sectionTitle: { fontSize: 18, fontWeight: '800', color: COLORS.text, marginBottom: 4 },
  sectionHint: { fontSize: 13, color: COLORS.textLight, lineHeight: 18, marginBottom: 12 },
  planControls: {
    backgroundColor: COLORS.backgroundLight,
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
  },
  emptyPlan: {
    backgroundColor: COLORS.backgroundLight,
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
  },
  emptyPlanText: { fontSize: 14, color: COLORS.textLight, lineHeight: 20 },
  divider: { height: 1, backgroundColor: COLORS.border, marginVertical: 8 },
  generatorCard: {
    backgroundColor: COLORS.backgroundLight,
    borderRadius: 16,
    padding: 16,
    marginTop: 12,
    marginBottom: 16,
  },
  askInterpretation: {
    fontSize: 13,
    color: COLORS.primary,
    fontWeight: '600',
    marginTop: 10,
    textAlign: 'center',
  },
});
