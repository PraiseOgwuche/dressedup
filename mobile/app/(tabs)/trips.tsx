import React, { useCallback, useState } from 'react';
import {
  Alert,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useFocusEffect } from 'expo-router';

import { useAuthStore } from '../../store/authStore';
import { THEME, FONTS, SHADOW, utilityTitle } from '../../constants/theme';
import { tripsAPI } from '../../services/api';
import { getApiErrorMessage } from '../../services/errors';
import { hasPremiumAccess, TripDayOutfit, TripPackingPlan, TripPlan } from '../../types';
import { Button } from '../../components/ui/Button';
import { CreateTripModal } from '../../components/trips/CreateTripModal';
import { TripPackingView } from '../../components/trips/TripPackingView';

function formatTripMeta(trip: TripPlan): string {
  if (trip.start_date && trip.end_date) {
    return `${trip.start_date} → ${trip.end_date} · ${trip.days} day${trip.days === 1 ? '' : 's'}`;
  }
  return `${trip.days} day${trip.days === 1 ? '' : 's'}`;
}

function dayLocks(days: TripDayOutfit[]) {
  return days.map((day) => ({
    day: day.day,
    top_id: day.top?.id ?? null,
    bottom_id: day.bottom?.id ?? null,
    shoes_id: day.shoes?.id ?? null,
    outerwear_id: day.outerwear?.id ?? null,
  }));
}

export default function TripsScreen() {
  const user = useAuthStore((state) => state.user);
  const premium = hasPremiumAccess(user);

  const [trips, setTrips] = useState<TripPlan[]>([]);
  const [loading, setLoading] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [editingTrip, setEditingTrip] = useState<TripPlan | null>(null);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [packing, setPacking] = useState<TripPackingPlan | null>(null);
  const [packingLoading, setPackingLoading] = useState(false);
  const [reshufflingDay, setReshufflingDay] = useState<number | null>(null);

  const loadTrips = useCallback(async () => {
    if (!premium) {
      setTrips([]);
      return;
    }
    setLoading(true);
    try {
      const plans = await tripsAPI.listPlans();
      setTrips(plans);
      if (selectedId && !plans.some((p) => p.id === selectedId)) {
        setSelectedId(null);
        setPacking(null);
      }
    } catch (error) {
      Alert.alert('Error', getApiErrorMessage(error, 'Could not load trips.'));
    } finally {
      setLoading(false);
    }
  }, [premium, selectedId]);

  useFocusEffect(
    useCallback(() => {
      loadTrips();
    }, [loadTrips]),
  );

  const loadPacking = async (planId: number) => {
    setSelectedId(planId);
    setPackingLoading(true);
    try {
      const plan = await tripsAPI.getPacking(planId);
      setPacking(plan);
    } catch (error) {
      setPacking(null);
      Alert.alert('Packing failed', getApiErrorMessage(error, 'Could not build a packing list.'));
    } finally {
      setPackingLoading(false);
    }
  };

  const reshuffleDay = async (day: TripDayOutfit) => {
    if (!packing || selectedId == null) return;
    setReshufflingDay(day.day);
    try {
      const next = await tripsAPI.reshuffleDay(selectedId, {
        day: day.day,
        locked_days: dayLocks(packing.days),
      });
      setPacking(next);
    } catch (error) {
      Alert.alert('Shuffle failed', getApiErrorMessage(error, 'Could not reshuffle that day.'));
    } finally {
      setReshufflingDay(null);
    }
  };

  const deleteTrip = (trip: TripPlan) => {
    Alert.alert('Delete trip', `Remove ${trip.destination}?`, [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete',
        style: 'destructive',
        onPress: async () => {
          try {
            await tripsAPI.deletePlan(trip.id);
            if (selectedId === trip.id) {
              setSelectedId(null);
              setPacking(null);
            }
            await loadTrips();
          } catch (error) {
            Alert.alert('Error', getApiErrorMessage(error, 'Could not delete trip.'));
          }
        },
      },
    ]);
  };

  const toggleComplete = async (trip: TripPlan) => {
    try {
      await tripsAPI.updatePlan(trip.id, { is_completed: !trip.is_completed });
      await loadTrips();
    } catch (error) {
      Alert.alert('Error', getApiErrorMessage(error, 'Could not update trip.'));
    }
  };

  const onTripSaved = async () => {
    await loadTrips();
    if (editingTrip && selectedId === editingTrip.id) {
      await loadPacking(editingTrip.id);
    }
  };

  const renderTrip = ({ item }: { item: TripPlan }) => {
    const active = selectedId === item.id;
    return (
      <View style={[styles.tripCard, active && styles.tripCardActive]}>
        <Pressable onPress={() => loadPacking(item.id)} style={styles.tripHeader}>
          <View style={styles.tripCopy}>
            <Text style={styles.tripDestination}>{item.destination}</Text>
            <Text style={styles.tripMeta}>{formatTripMeta(item)}</Text>
            {item.is_completed ? <Text style={styles.completedBadge}>Packed / done</Text> : null}
          </View>
          <Text style={styles.tripAction}>{active ? '▼' : '▶'}</Text>
        </Pressable>
        <View style={styles.tripActions}>
          <Pressable style={styles.smallBtn} onPress={() => loadPacking(item.id)}>
            <Text style={styles.smallBtnText}>{packingLoading && active ? 'Loading…' : 'What to pack'}</Text>
          </Pressable>
          <Pressable
            style={styles.smallBtnSecondary}
            onPress={() => {
              setEditingTrip(item);
              setCreateOpen(true);
            }}
          >
            <Text style={styles.smallBtnSecondaryText}>Edit</Text>
          </Pressable>
          <Pressable style={styles.smallBtn} onPress={() => toggleComplete(item)}>
            <Text style={styles.smallBtnText}>{item.is_completed ? 'Reopen' : 'Mark done'}</Text>
          </Pressable>
          <Pressable style={styles.smallBtnDanger} onPress={() => deleteTrip(item)}>
            <Text style={styles.smallBtnDangerText}>Delete</Text>
          </Pressable>
        </View>
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Trips</Text>
        <Text style={styles.subtitle}>
          Weather-aware outfits per day, plus one smart suitcase list from your closet.
        </Text>
        {premium ? (
          <Button
            title="+ New trip"
            onPress={() => {
              setEditingTrip(null);
              setCreateOpen(true);
            }}
            style={styles.newBtn}
          />
        ) : null}
      </View>

      {!premium ? (
        <View style={styles.lockedBox}>
          <Text style={styles.lockedEmoji}>✈️</Text>
          <Text style={styles.lockedTitle}>Trip planner is premium</Text>
          <Text style={styles.lockedBody}>
            Your trial includes packing plans with live weather when you add trip dates. Check You →
            premium status, or contact us to upgrade.
          </Text>
        </View>
      ) : (
        <ScrollView
          contentContainerStyle={styles.scroll}
          refreshControl={<RefreshControl refreshing={loading} onRefresh={loadTrips} />}
        >
          {trips.length === 0 && !loading ? (
            <View style={styles.empty}>
              <Text style={styles.emptyEmoji}>🧳</Text>
              <Text style={styles.emptyTitle}>No trips yet</Text>
              <Text style={styles.emptyBody}>
                Add a destination and dates — we will dress you for each day and tell you exactly
                what to pack once.
              </Text>
              <Button
                title="Plan your first trip"
                onPress={() => {
                  setEditingTrip(null);
                  setCreateOpen(true);
                }}
              />
            </View>
          ) : (
            trips.map((item) => (
              <View key={item.id}>{renderTrip({ item })}</View>
            ))
          )}

          {packing && selectedId === packing.trip.id ? (
            <View style={styles.packingSection}>
              <TripPackingView
                plan={packing}
                onReshuffleDay={reshuffleDay}
                reshufflingDay={reshufflingDay}
              />
            </View>
          ) : null}
        </ScrollView>
      )}

      <CreateTripModal
        visible={createOpen}
        trip={editingTrip}
        onClose={() => {
          setCreateOpen(false);
          setEditingTrip(null);
        }}
        onSaved={onTripSaved}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: THEME.utility.background },
  header: {
    paddingHorizontal: 22,
    paddingTop: 12,
    paddingBottom: 14,
    borderBottomWidth: 1,
    borderBottomColor: THEME.utility.border,
    gap: 8,
  },
  title: { ...utilityTitle(28), textAlign: 'left' },
  subtitle: { fontSize: 14, lineHeight: 20, color: THEME.utility.textMuted },
  newBtn: { alignSelf: 'flex-start', marginTop: 4 },
  scroll: { padding: 22, paddingBottom: 40, gap: 16 },
  tripCard: {
    backgroundColor: THEME.utility.surface,
    borderRadius: 18,
    borderWidth: 1,
    borderColor: THEME.utility.border,
    overflow: 'hidden',
    marginBottom: 12,
    ...SHADOW.soft,
  },
  tripCardActive: { borderColor: THEME.brand.ink },
  tripHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    gap: 12,
  },
  tripCopy: { flex: 1, gap: 4 },
  tripDestination: {
    fontFamily: FONTS.sans,
    fontSize: 18,
    fontWeight: '700',
    color: THEME.utility.text,
  },
  tripMeta: { fontSize: 13, color: THEME.utility.textMuted },
  completedBadge: {
    fontSize: 11,
    fontWeight: '700',
    color: THEME.shared.success,
    textTransform: 'uppercase',
    letterSpacing: 0.6,
  },
  tripAction: { fontSize: 14, color: THEME.utility.textMuted },
  tripActions: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    paddingHorizontal: 16,
    paddingBottom: 14,
  },
  smallBtn: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 12,
    backgroundColor: THEME.brand.ink,
  },
  smallBtnText: { color: '#fff', fontSize: 12, fontWeight: '700' },
  smallBtnSecondary: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 12,
    backgroundColor: THEME.utility.surfaceMuted,
    borderWidth: 1,
    borderColor: THEME.utility.border,
  },
  smallBtnSecondaryText: { fontSize: 12, fontWeight: '700', color: THEME.brand.ink },
  smallBtnDanger: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: THEME.utility.border,
    backgroundColor: THEME.utility.surfaceMuted,
  },
  smallBtnDangerText: { fontSize: 12, fontWeight: '600', color: THEME.utility.textMuted },
  packingSection: { marginTop: 8 },
  empty: {
    alignItems: 'center',
    padding: 28,
    gap: 10,
    backgroundColor: THEME.utility.surfaceMuted,
    borderRadius: 20,
    ...SHADOW.soft,
  },
  emptyEmoji: { fontSize: 48 },
  emptyTitle: { fontSize: 18, fontWeight: '700', color: THEME.utility.text },
  emptyBody: { fontSize: 14, color: THEME.utility.textMuted, textAlign: 'center', lineHeight: 20 },
  lockedBox: {
    margin: 22,
    padding: 28,
    borderRadius: 20,
    backgroundColor: THEME.utility.surfaceMuted,
    alignItems: 'center',
    gap: 10,
    ...SHADOW.soft,
  },
  lockedEmoji: { fontSize: 48 },
  lockedTitle: { fontSize: 18, fontWeight: '700', color: THEME.utility.text },
  lockedBody: { fontSize: 14, color: THEME.utility.textMuted, textAlign: 'center', lineHeight: 20 },
});
