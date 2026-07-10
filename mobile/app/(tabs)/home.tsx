import React, { useCallback, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Alert,
  TextInput,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useFocusEffect, useRouter } from 'expo-router';
import { useAuthStore } from '../../store/authStore';
import { useRoutineStore } from '../../store/routineStore';
import { useClosetStore } from '../../store/closetStore';
import { TAXONOMY } from '../../constants/config';
import { THEME, FONTS, editorialTitle, sectionLabel } from '../../constants/theme';
import { closetAPI, outfitAPI, socialAPI } from '../../services/api';
import { getApiErrorMessage } from '../../services/errors';
import { ClosetItem, OutfitSuggestion, DailyPlan, PlanActivity, OutfitSharePayload } from '../../types';
import { Button } from '../../components/ui/Button';
import { ChipSelect } from '../../components/ui/ChipSelect';
import { CollapsibleSection } from '../../components/ui/CollapsibleSection';
import { OutfitCard, OutfitSlotKey } from '../../components/OutfitCard';
import { OutfitHero } from '../../components/OutfitHero';
import { ShareFitModal } from '../../components/ShareFitModal';
import { TripTeaser } from '../../components/trips/TripTeaser';

const firstName = (full?: string) => (full?.trim().split(/\s+/)[0] || 'there');

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
  const [shareOutfit, setShareOutfit] = useState<OutfitSharePayload | null>(null);
  const [shareVisible, setShareVisible] = useState(false);
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
      // non-blocking
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
      Alert.alert('Say more', 'Try: “Dress me for a cold work day, quiet luxury”.');
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

  const promptShareAfterWear = (outfit: OutfitSharePayload) => {
    Alert.alert('Logged', 'Marked as worn.', [
      { text: 'Done', style: 'cancel' },
      {
        text: 'Share to feed',
        onPress: () => {
          setShareOutfit(outfit);
          setShareVisible(true);
        },
      },
    ]);
  };

  const handleShareFit = async (payload: {
    caption?: string;
    photo?: { uri: string; name?: string | null; mimeType?: string | null } | null;
  }) => {
    if (!shareOutfit) return;
    await socialAPI.createPost({
      top_id: shareOutfit.top?.id,
      bottom_id: shareOutfit.bottom?.id,
      shoes_id: shareOutfit.shoes?.id,
      outerwear_id: shareOutfit.outerwear?.id,
      caption: payload.caption,
      occasion: occasion || undefined,
      photo: payload.photo,
    });
    Alert.alert('Shared', 'Your fit is on the feed.');
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
      promptShareAfterWear({
        top: suggestion?.top,
        bottom: suggestion?.bottom,
        shoes: suggestion?.shoes,
        outerwear: suggestion?.outerwear,
      });
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
      promptShareAfterWear({
        top: activity.top,
        bottom: activity.bottom,
        shoes: activity.shoes,
        outerwear: activity.outerwear,
      });
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
      Alert.alert('Unable to swap', 'No better alternative found for that piece.');
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
    <View style={styles.root}>
      <ScrollView bounces showsVerticalScrollIndicator={false}>
        {/* —— Editorial hero zone —— */}
        <SafeAreaView edges={['top']} style={styles.editorialZone}>
          <Text style={styles.brand}>DRESSEDUP</Text>
          <Text style={styles.greeting}>Good morning, {firstName(user?.full_name)}</Text>
          <Text style={styles.heroSubtitle}>
            {items.length > 0
              ? `Today's look · ${items.length} piece${items.length === 1 ? '' : 's'} · ${items.filter((i) => i.is_clean).length} clean`
              : "Today's look"}
          </Text>

          <TripTeaser user={user} />

          {items.length === 0 ? (
            <View style={styles.emptyCloset}>
              <Text style={styles.emptyClosetText}>
                Start with a few pieces in your closet — a flat-lay photo works great.
              </Text>
              <Button title="Open closet" variant="editorial" onPress={() => router.push('/(tabs)/closet')} />
            </View>
          ) : (
            <OutfitHero
              top={suggestion?.top}
              bottom={suggestion?.bottom}
              shoes={suggestion?.shoes}
              outerwear={suggestion?.outerwear}
              rationale={suggestion?.rationale}
              stylingNote={suggestion?.styling_note}
              interpretation={askInterpretation}
              loading={isLoading || askLoading}
              onShuffle={loadSuggestion}
              onWore={handleWoreSuggestion}
              woreLoading={wearing}
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
            />
          )}

          {laundry?.laundry_due ? (
            <Text style={styles.laundryHint}>🧺 {laundry.message}</Text>
          ) : null}

          <View style={styles.askRow}>
            <TextInput
              style={styles.askInput}
              placeholder="Dress me for…"
              placeholderTextColor={THEME.editorial.textMuted}
              value={askQuery}
              onChangeText={setAskQuery}
              onSubmitEditing={handleAsk}
              returnKeyType="go"
            />
            <Button title="Ask" variant="editorial" loading={askLoading} onPress={handleAsk} style={styles.askBtn} />
          </View>
        </SafeAreaView>

        {/* —— Utility zone —— */}
        <View style={styles.utilityZone}>
          <Text style={styles.utilityHeading}>More for today</Text>

          <CollapsibleSection title="Plan my day" subtitle="Work, gym, dates — we pack the rest">
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
            <Button title="Build plan" loading={planLoading} onPress={loadPlan} />
            {plan?.activities?.map((activity) => (
              <OutfitCard
                key={activity.activity}
                variant="utility"
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
            ))}
          </CollapsibleSection>

          <CollapsibleSection title="My routine" subtitle="One tap from saved preferences">
            <Button title="Send me my plan" loading={routineLoading} onPress={handleSendMyPlan} />
          </CollapsibleSection>

          <CollapsibleSection title="Fine-tune outfit" subtitle="Occasion, vibe, regenerate">
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
            <Button title="Regenerate" loading={isLoading} onPress={loadSuggestion} />
          </CollapsibleSection>
        </View>
      </ScrollView>
      <ShareFitModal
        visible={shareVisible}
        outfit={shareOutfit}
        occasion={occasion || undefined}
        onClose={() => {
          setShareVisible(false);
          setShareOutfit(null);
        }}
        onShare={handleShareFit}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: THEME.utility.background },
  editorialZone: {
    backgroundColor: THEME.editorial.background,
    paddingHorizontal: 22,
    paddingBottom: 28,
    borderBottomLeftRadius: 28,
    borderBottomRightRadius: 28,
  },
  brand: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 3,
    color: THEME.editorial.accentDark,
    textAlign: 'center',
    marginTop: 8,
    textTransform: 'uppercase',
  },
  greeting: {
    ...editorialTitle(32),
    marginTop: 16,
    textAlign: 'center',
  },
  heroSubtitle: {
    fontSize: 13,
    color: THEME.editorial.textMuted,
    textAlign: 'center',
    marginTop: 6,
    marginBottom: 20,
    letterSpacing: 0.5,
  },
  emptyCloset: {
    backgroundColor: THEME.editorial.surface,
    borderRadius: 20,
    padding: 24,
    alignItems: 'center',
    gap: 12,
  },
  emptyClosetText: {
    fontSize: 14,
    color: THEME.editorial.textMuted,
    textAlign: 'center',
    lineHeight: 20,
  },
  laundryHint: {
    fontSize: 13,
    color: THEME.shared.warning,
    marginTop: 12,
    textAlign: 'center',
  },
  askRow: { flexDirection: 'row', gap: 10, marginTop: 20, alignItems: 'center' },
  askInput: {
    flex: 1,
    backgroundColor: THEME.editorial.pill,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: THEME.editorial.border,
    paddingHorizontal: 16,
    paddingVertical: Platform.OS === 'ios' ? 14 : 10,
    fontSize: 15,
    color: THEME.editorial.text,
    fontFamily: FONTS.sans,
  },
  askBtn: { minWidth: 88, minHeight: 48, paddingVertical: 12 },
  utilityZone: {
    paddingHorizontal: 20,
    paddingTop: 24,
    paddingBottom: 40,
  },
  utilityHeading: {
    ...sectionLabel(),
    marginBottom: 14,
  },
});
