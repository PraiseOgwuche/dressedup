import React from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { THEME, FONTS, SHADOW } from '../../constants/theme';
import { StyleProfile } from '../../types';

type Props = {
  profile: StyleProfile | null;
  loading?: boolean;
};

const ACTIVITY_LABELS: { key: keyof StyleProfile['activity']; label: string }[] = [
  { key: 'wore', label: 'Wears' },
  { key: 'likes', label: 'Likes' },
  { key: 'swaps', label: 'Swaps' },
  { key: 'shop_explores', label: 'Shop' },
];

export function StyleProfileCard({ profile, loading }: Props) {
  if (loading) {
    return (
      <View style={styles.card}>
        <Text style={styles.title}>Your style profile</Text>
        <Text style={styles.hint}>Learning your taste…</Text>
      </View>
    );
  }

  if (!profile) return null;

  return (
    <View style={styles.card}>
      <Text style={styles.kicker}>Personalization</Text>
      <Text style={styles.title}>{profile.headline}</Text>
      <Text style={styles.summary}>{profile.summary}</Text>

      {profile.formality_zone ? (
        <View style={styles.zonePill}>
          <Text style={styles.zoneText}>
            Sweet spot · {profile.formality_zone.replace('-', ' ')}
          </Text>
        </View>
      ) : null}

      {profile.top_colors.length > 0 ? (
        <View style={styles.section}>
          <Text style={styles.sectionLabel}>Go-to colors</Text>
          <View style={styles.chipRow}>
            {profile.top_colors.map((color) => (
              <View key={color.label} style={styles.chip}>
                <Text style={styles.chipText}>{color.label}</Text>
              </View>
            ))}
          </View>
        </View>
      ) : null}

      {profile.top_categories.length > 0 ? (
        <View style={styles.section}>
          <Text style={styles.sectionLabel}>Closet mix</Text>
          <View style={styles.barList}>
            {profile.top_categories.map((cat) => {
              const max = profile.top_categories[0]?.value || 1;
              const width = `${Math.max(18, Math.round((cat.value / max) * 100))}%`;
              return (
                <View key={cat.label} style={styles.barRow}>
                  <Text style={styles.barLabel}>{cat.label}</Text>
                  <View style={styles.barTrack}>
                    <View style={[styles.barFill, { width: width as `${number}%` }]} />
                  </View>
                  <Text style={styles.barValue}>{cat.value}</Text>
                </View>
              );
            })}
          </View>
        </View>
      ) : null}

      <View style={styles.activityRow}>
        {ACTIVITY_LABELS.map(({ key, label }) => (
          <View key={key} style={styles.activityPill}>
            <Text style={styles.activityValue}>{profile.activity[key]}</Text>
            <Text style={styles.activityLabel}>{label}</Text>
          </View>
        ))}
      </View>

      {profile.insights.map((line) => (
        <Text key={line} style={styles.insight}>
          · {line}
        </Text>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: THEME.utility.surface,
    borderRadius: 20,
    padding: 18,
    borderWidth: 1,
    borderColor: THEME.utility.border,
    gap: 12,
    ...SHADOW.soft,
  },
  kicker: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1.1,
    textTransform: 'uppercase',
    color: THEME.utility.textMuted,
  },
  title: {
    fontFamily: FONTS.sans,
    fontSize: 20,
    fontWeight: '700',
    color: THEME.utility.text,
  },
  summary: {
    fontSize: 14,
    lineHeight: 20,
    color: THEME.utility.textMuted,
  },
  hint: {
    fontSize: 14,
    color: THEME.utility.textMuted,
    fontStyle: 'italic',
  },
  zonePill: {
    alignSelf: 'flex-start',
    backgroundColor: THEME.brand.sand,
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  zoneText: {
    fontSize: 12,
    fontWeight: '700',
    color: THEME.utility.text,
    textTransform: 'capitalize',
  },
  section: { gap: 8 },
  sectionLabel: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.8,
    textTransform: 'uppercase',
    color: THEME.utility.textMuted,
  },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: {
    backgroundColor: THEME.utility.surfaceMuted,
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderWidth: 1,
    borderColor: THEME.utility.border,
  },
  chipText: { fontSize: 12, fontWeight: '600', color: THEME.utility.text },
  barList: { gap: 8 },
  barRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  barLabel: { width: 72, fontSize: 12, color: THEME.utility.text },
  barTrack: {
    flex: 1,
    height: 8,
    borderRadius: 4,
    backgroundColor: THEME.utility.surfaceMuted,
    overflow: 'hidden',
  },
  barFill: {
    height: '100%',
    borderRadius: 4,
    backgroundColor: THEME.brand.ink,
  },
  barValue: { width: 20, fontSize: 12, fontWeight: '700', color: THEME.utility.textMuted, textAlign: 'right' },
  activityRow: { flexDirection: 'row', gap: 8, flexWrap: 'wrap' },
  activityPill: {
    flex: 1,
    minWidth: 68,
    backgroundColor: THEME.utility.surfaceMuted,
    borderRadius: 12,
    paddingVertical: 10,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: THEME.utility.border,
  },
  activityValue: { fontSize: 16, fontWeight: '800', color: THEME.utility.text },
  activityLabel: {
    marginTop: 2,
    fontSize: 10,
    fontWeight: '600',
    color: THEME.utility.textMuted,
    textTransform: 'uppercase',
  },
  insight: {
    fontSize: 13,
    lineHeight: 19,
    color: THEME.utility.text,
  },
});
