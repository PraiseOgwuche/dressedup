import React from 'react';
import { View, Text, StyleSheet, Image } from 'react-native';
import { COLORS, mediaUrl } from '../constants/config';
import { ClosetItem } from '../types';
import { Button } from './ui/Button';

const SLOT_EMOJI: Record<string, string> = {
  Top: '👕',
  Bottom: '👖',
  Shoes: '👟',
  Outerwear: '🧥',
};

interface OutfitCardProps {
  title?: string;
  badge?: string;
  rationale?: string | null;
  top?: ClosetItem | null;
  bottom?: ClosetItem | null;
  shoes?: ClosetItem | null;
  outerwear?: ClosetItem | null;
  alternatives?: ClosetItem[];
  packingList?: ClosetItem[];
  onWore?: () => void;
  woreLoading?: boolean;
}

export function OutfitCard({
  title,
  badge,
  rationale,
  top,
  bottom,
  shoes,
  outerwear,
  alternatives,
  packingList,
  onWore,
  woreLoading,
}: OutfitCardProps) {
  const slots: { label: string; item?: ClosetItem | null }[] = [
    { label: 'Top', item: top },
    { label: 'Bottom', item: bottom },
    { label: 'Shoes', item: shoes },
    { label: 'Outerwear', item: outerwear },
  ];
  const hasOutfit = !!(top || bottom || shoes);

  return (
    <View style={styles.card}>
      <View style={styles.titleRow}>
        <Text style={styles.title}>{title || 'Outfit'}</Text>
        {!!badge && (
          <View style={[styles.badge, badge === 'PACK' && styles.badgePack]}>
            <Text style={[styles.badgeText, badge === 'PACK' && styles.badgeTextPack]}>{badge}</Text>
          </View>
        )}
      </View>

      {!!rationale && (
        <View style={styles.rationalePill}>
          <Text style={styles.rationalePillText}>{rationale}</Text>
        </View>
      )}

      {slots.map((slot) => {
        const thumb = slot.item ? mediaUrl(slot.item.thumbnail_url ?? slot.item.image_url) : undefined;
        const fallbackName = slot.label === 'Outerwear' ? 'Optional' : `No ${slot.label.toLowerCase()} yet`;
        return (
          <View key={slot.label} style={[styles.slotRow, !slot.item && styles.slotRowEmpty]}>
            <View style={styles.slotThumb}>
              {thumb ? (
                <Image source={{ uri: thumb }} style={styles.slotImage} resizeMode="cover" />
              ) : (
                <Text style={styles.slotEmoji}>{SLOT_EMOJI[slot.label]}</Text>
              )}
            </View>
            <View style={styles.slotInfo}>
              <Text style={styles.slotLabel}>{slot.label.toUpperCase()}</Text>
              <Text style={[styles.slotName, !slot.item && styles.slotNameEmpty]} numberOfLines={1}>
                {slot.item?.name || fallbackName}
              </Text>
              {slot.item?.brand ? <Text style={styles.slotMeta}>{slot.item.brand}</Text> : null}
            </View>
          </View>
        );
      })}

      {!!packingList?.length && (
        <View style={styles.packSection}>
          <Text style={styles.packHeading}>👜 Pack these</Text>
          {packingList.map((item) => (
            <Text key={item.id} style={styles.packItem} numberOfLines={1}>
              • {item.name}
              {item.brand ? `  ·  ${item.brand}` : ''}
            </Text>
          ))}
        </View>
      )}

      {!!alternatives?.length && (
        <View style={styles.altSection}>
          <Text style={styles.altHeading}>Alternatives</Text>
          <View style={styles.altRow}>
            {alternatives.map((item) => (
              <View key={item.id} style={styles.altChip}>
                <Text style={styles.altChipText} numberOfLines={1}>
                  {item.name}
                </Text>
              </View>
            ))}
          </View>
        </View>
      )}

      {hasOutfit && onWore && (
        <Button title="Wore this outfit" loading={woreLoading} onPress={onWore} style={styles.woreBtn} />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#fff',
    borderRadius: 20,
    padding: 18,
    borderWidth: 1,
    borderColor: COLORS.border,
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: 4 },
    elevation: 2,
    marginBottom: 16,
  },
  titleRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  title: { fontSize: 22, fontWeight: '800', color: COLORS.text, flex: 1 },
  badge: {
    backgroundColor: COLORS.primary,
    borderRadius: 12,
    paddingHorizontal: 10,
    paddingVertical: 4,
    marginLeft: 8,
  },
  badgePack: { backgroundColor: '#FFE7C2' },
  badgeText: { fontSize: 11, fontWeight: '800', color: '#fff', letterSpacing: 0.5 },
  badgeTextPack: { color: '#9A6400' },
  rationalePill: {
    alignSelf: 'flex-start',
    backgroundColor: '#EEF0FF',
    borderRadius: 20,
    paddingHorizontal: 12,
    paddingVertical: 6,
    marginTop: 10,
    marginBottom: 6,
  },
  rationalePillText: { fontSize: 12, color: COLORS.primary, fontWeight: '700' },
  slotRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
  },
  slotRowEmpty: { opacity: 0.5 },
  slotThumb: {
    width: 56,
    height: 56,
    borderRadius: 12,
    backgroundColor: COLORS.backgroundLight,
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
  },
  slotImage: { width: '100%', height: '100%' },
  slotEmoji: { fontSize: 28 },
  slotInfo: { flex: 1, marginLeft: 14 },
  slotLabel: { fontSize: 11, fontWeight: '700', color: COLORS.textLight, letterSpacing: 1 },
  slotName: { fontSize: 17, fontWeight: '700', color: COLORS.text, marginTop: 2 },
  slotNameEmpty: { fontWeight: '500', color: COLORS.textLight },
  slotMeta: { fontSize: 13, color: COLORS.textLight, marginTop: 1 },
  packSection: {
    marginTop: 14,
    backgroundColor: '#FFF8EE',
    borderRadius: 12,
    padding: 12,
  },
  packHeading: { fontSize: 13, fontWeight: '800', color: '#9A6400', marginBottom: 6 },
  packItem: { fontSize: 14, color: COLORS.text, marginTop: 2 },
  altSection: { marginTop: 16 },
  altHeading: { fontSize: 13, fontWeight: '700', color: COLORS.textLight, marginBottom: 8 },
  altRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  altChip: {
    backgroundColor: COLORS.backgroundLight,
    borderRadius: 16,
    paddingHorizontal: 12,
    paddingVertical: 8,
    maxWidth: '100%',
  },
  altChipText: { fontSize: 13, color: COLORS.text, fontWeight: '600' },
  woreBtn: { marginTop: 18 },
});
