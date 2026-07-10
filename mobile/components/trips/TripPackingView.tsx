import React from 'react';
import { Image, ScrollView, StyleSheet, Text, View } from 'react-native';

import { mediaUrl } from '../../constants/config';
import { THEME, FONTS, SHADOW } from '../../constants/theme';
import { TripPackingPlan } from '../../types';
import { OutfitCard } from '../OutfitCard';

type Props = {
  plan: TripPackingPlan;
};

export function TripPackingView({ plan }: Props) {
  return (
    <View style={styles.wrap}>
      <View style={styles.summaryCard}>
        <Text style={styles.summaryTitle}>{plan.trip.destination}</Text>
        <Text style={styles.summaryText}>{plan.summary}</Text>
        {plan.weather_note ? <Text style={styles.weatherNote}>{plan.weather_note}</Text> : null}
      </View>

      <Text style={styles.sectionTitle}>Day by day</Text>
      {plan.days.map((day) => (
        <OutfitCard
          key={day.day}
          variant="utility"
          title={day.title}
          badge={day.weather_tag?.toUpperCase()}
          rationale={day.weather_summary || day.rationale}
          top={day.top}
          bottom={day.bottom}
          shoes={day.shoes}
          outerwear={day.outerwear}
        />
      ))}

      <Text style={styles.sectionTitle}>Suitcase ({plan.packing_list.length})</Text>
      <Text style={styles.suitcaseHint}>Pack each piece once — reused across days where possible.</Text>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.suitcaseRow}>
        {plan.packing_list.map((item) => {
          const uri = mediaUrl(item.thumbnail_url ?? item.image_url);
          return (
            <View key={item.id} style={styles.suitcaseItem}>
              {uri ? (
                <Image source={{ uri }} style={styles.suitcaseImage} resizeMode="cover" />
              ) : (
                <View style={styles.suitcasePlaceholder}>
                  <Text>👕</Text>
                </View>
              )}
              <Text style={styles.suitcaseName} numberOfLines={2}>
                {item.name}
              </Text>
              <Text style={styles.suitcaseMeta}>{item.category}</Text>
            </View>
          );
        })}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { gap: 14 },
  summaryCard: {
    backgroundColor: THEME.brand.sand,
    borderRadius: 18,
    padding: 16,
    gap: 6,
    ...SHADOW.soft,
  },
  summaryTitle: {
    fontFamily: FONTS.sans,
    fontSize: 20,
    fontWeight: '700',
    color: THEME.utility.text,
  },
  summaryText: { fontSize: 14, lineHeight: 20, color: THEME.utility.text },
  weatherNote: { fontSize: 13, lineHeight: 18, color: THEME.utility.textMuted, fontStyle: 'italic' },
  sectionTitle: {
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 0.8,
    textTransform: 'uppercase',
    color: THEME.utility.textMuted,
    marginTop: 4,
  },
  suitcaseHint: { fontSize: 13, color: THEME.utility.textMuted, marginBottom: 4 },
  suitcaseRow: { gap: 10, paddingVertical: 4 },
  suitcaseItem: {
    width: 92,
    backgroundColor: THEME.utility.surface,
    borderRadius: 14,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: THEME.utility.border,
  },
  suitcaseImage: { width: '100%', height: 100, backgroundColor: THEME.editorial.pill },
  suitcasePlaceholder: {
    height: 100,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: THEME.editorial.pill,
  },
  suitcaseName: {
    fontSize: 11,
    fontWeight: '600',
    paddingHorizontal: 8,
    paddingTop: 8,
    color: THEME.utility.text,
    minHeight: 32,
  },
  suitcaseMeta: {
    fontSize: 10,
    color: THEME.utility.textMuted,
    paddingHorizontal: 8,
    paddingBottom: 8,
    textTransform: 'capitalize',
  },
});
