import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

import { THEME } from '../constants/theme';
import { StreakStats } from '../types';

interface StreakBadgeProps {
  streak: StreakStats | null;
  compact?: boolean;
}

export function StreakBadge({ streak, compact }: StreakBadgeProps) {
  if (!streak) return null;
  const count = streak.current_streak;
  const label =
    count === 0
      ? 'Log a fit to start your streak'
      : `${count} day${count === 1 ? '' : 's'} streak`;

  return (
    <View style={[styles.badge, compact && styles.badgeCompact, count > 0 && styles.badgeActive]}>
      {count > 0 && <Text style={styles.flame}>🔥</Text>}
      <Text style={[styles.text, compact && styles.textCompact, count > 0 && styles.textActive]}>
        {label}
      </Text>
    </View>
  );
}

interface StreakCardProps {
  streak: StreakStats | null;
}

export function StreakCard({ streak }: StreakCardProps) {
  if (!streak) return null;

  return (
    <View style={styles.card}>
      <View style={styles.cardHeader}>
        <Text style={styles.cardTitle}>Fit streak</Text>
        {streak.current_streak > 0 ? (
          <Text style={styles.cardFlame}>🔥 {streak.current_streak}</Text>
        ) : null}
      </View>
      <Text style={styles.cardHint}>
        {streak.current_streak > 0
          ? 'Keep logging what you wear or sharing fits to build your streak.'
          : 'Log an outfit on Home or share a fit to start a streak.'}
      </Text>
      <View style={styles.metrics}>
        <View style={styles.metric}>
          <Text style={styles.metricValue}>{streak.current_streak}</Text>
          <Text style={styles.metricLabel}>Current</Text>
        </View>
        <View style={styles.metric}>
          <Text style={styles.metricValue}>{streak.longest_streak}</Text>
          <Text style={styles.metricLabel}>Best</Text>
        </View>
        <View style={styles.metric}>
          <Text style={styles.metricValue}>{streak.total_fit_days}</Text>
          <Text style={styles.metricLabel}>Fit days</Text>
        </View>
        <View style={styles.metric}>
          <Text style={styles.metricValue}>{streak.active_this_week}</Text>
          <Text style={styles.metricLabel}>This week</Text>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    alignSelf: 'flex-start',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 999,
    backgroundColor: THEME.utility.surfaceMuted,
  },
  badgeCompact: {
    paddingVertical: 6,
  },
  badgeActive: {
    backgroundColor: THEME.brand.sand,
  },
  flame: {
    fontSize: 14,
  },
  text: {
    fontSize: 13,
    fontWeight: '600',
    color: THEME.utility.textMuted,
  },
  textCompact: {
    fontSize: 12,
  },
  textActive: {
    color: THEME.utility.text,
  },
  card: {
    backgroundColor: THEME.utility.surface,
    borderRadius: 18,
    padding: 16,
    borderWidth: 1,
    borderColor: THEME.utility.border,
    gap: 10,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: THEME.utility.text,
  },
  cardFlame: {
    fontSize: 16,
    fontWeight: '700',
    color: THEME.utility.text,
  },
  cardHint: {
    fontSize: 13,
    lineHeight: 18,
    color: THEME.utility.textMuted,
  },
  metrics: {
    flexDirection: 'row',
    gap: 8,
  },
  metric: {
    flex: 1,
    backgroundColor: THEME.utility.surfaceMuted,
    borderRadius: 12,
    paddingVertical: 10,
    alignItems: 'center',
  },
  metricValue: {
    fontSize: 18,
    fontWeight: '700',
    color: THEME.utility.text,
  },
  metricLabel: {
    fontSize: 11,
    color: THEME.utility.textMuted,
    marginTop: 2,
  },
});
