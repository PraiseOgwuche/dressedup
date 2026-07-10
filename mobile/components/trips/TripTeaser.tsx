import React, { useCallback, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { useFocusEffect, useRouter } from 'expo-router';

import { THEME, SHADOW } from '../../constants/theme';
import { tripsAPI } from '../../services/api';
import { hasPremiumAccess, TripPlan, User } from '../../types';

type Props = {
  user: User | null;
};

function formatTripDates(trip: TripPlan): string {
  if (trip.start_date && trip.end_date) {
    return `${trip.start_date} → ${trip.end_date}`;
  }
  return `${trip.days} day${trip.days === 1 ? '' : 's'}`;
}

export function TripTeaser({ user }: Props) {
  const router = useRouter();
  const [upcoming, setUpcoming] = useState<TripPlan | null>(null);

  const load = useCallback(async () => {
    if (!hasPremiumAccess(user)) {
      setUpcoming(null);
      return;
    }
    try {
      const plans = await tripsAPI.listPlans();
      const active = plans.find((p) => !p.is_completed);
      setUpcoming(active ?? plans[0] ?? null);
    } catch {
      setUpcoming(null);
    }
  }, [user]);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load]),
  );

  return (
    <Pressable style={styles.card} onPress={() => router.push('/(tabs)/trips')}>
      <View style={styles.copy}>
        <Text style={styles.eyebrow}>Trip planner</Text>
        {upcoming ? (
          <>
            <Text style={styles.title}>{upcoming.destination}</Text>
            <Text style={styles.body}>{formatTripDates(upcoming)} · tap to pack</Text>
          </>
        ) : (
          <>
            <Text style={styles.title}>Planning a trip?</Text>
            <Text style={styles.body}>
              Day-by-day outfits + a deduped suitcase list from your closet.
            </Text>
          </>
        )}
      </View>
      <Text style={styles.chevron}>→</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginHorizontal: 22,
    marginTop: 16,
    padding: 16,
    borderRadius: 18,
    backgroundColor: THEME.utility.surface,
    borderWidth: 1,
    borderColor: THEME.utility.border,
    ...SHADOW.soft,
  },
  copy: { flex: 1, gap: 4 },
  eyebrow: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.8,
    textTransform: 'uppercase',
    color: THEME.editorial.accentDark,
  },
  title: { fontSize: 17, fontWeight: '700', color: THEME.utility.text },
  body: { fontSize: 13, lineHeight: 18, color: THEME.utility.textMuted },
  chevron: { fontSize: 22, color: THEME.brand.ink, fontWeight: '300' },
});
