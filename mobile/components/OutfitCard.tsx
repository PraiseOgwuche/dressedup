import React from 'react';
import { View, Text, StyleSheet, Image, Pressable, ActivityIndicator } from 'react-native';
import { COLORS, mediaUrl } from '../constants/config';
import { THEME, SHADOW, utilityTitle } from '../constants/theme';
import { ClosetItem } from '../types';
import { Button } from './ui/Button';

const SLOT_EMOJI: Record<string, string> = {
  Top: '👕',
  Bottom: '👖',
  Shoes: '👟',
  Outerwear: '🧥',
  Dress: '👗',
};

export type OutfitSlotKey = 'top' | 'bottom' | 'shoes' | 'outerwear' | 'dress';

const SLOT_KEY: Record<string, OutfitSlotKey> = {
  Top: 'top',
  Bottom: 'bottom',
  Shoes: 'shoes',
  Outerwear: 'outerwear',
  Dress: 'dress',
};

interface OutfitCardProps {
  title?: string;
  badge?: string;
  variant?: 'default' | 'utility';
  rationale?: string | null;
  top?: ClosetItem | null;
  bottom?: ClosetItem | null;
  shoes?: ClosetItem | null;
  outerwear?: ClosetItem | null;
  dress?: ClosetItem | null;
  alternatives?: ClosetItem[];
  packingList?: ClosetItem[];
  onWore?: () => void;
  woreLoading?: boolean;
  onLike?: () => void;
  onDislike?: () => void;
  feedbackLoading?: boolean;
  onSwapSlot?: (slot: OutfitSlotKey) => void;
  swappingSlot?: OutfitSlotKey | null;
}

export function OutfitCard({
  title,
  badge,
  variant = 'default',
  rationale,
  top,
  bottom,
  shoes,
  outerwear,
  dress,
  alternatives,
  packingList,
  onWore,
  woreLoading,
  onLike,
  onDislike,
  feedbackLoading,
  onSwapSlot,
  swappingSlot,
}: OutfitCardProps) {
  const slots: { label: string; item?: ClosetItem | null }[] = dress
    ? [
        { label: 'Dress', item: dress },
        { label: 'Shoes', item: shoes },
        { label: 'Outerwear', item: outerwear },
      ]
    : [
        { label: 'Top', item: top },
        { label: 'Bottom', item: bottom },
        { label: 'Shoes', item: shoes },
        { label: 'Outerwear', item: outerwear },
      ];
  const hasOutfit = !!(top || bottom || shoes || dress);

  return (
    <View style={[styles.card, variant === 'utility' && styles.cardUtility]}>
      <View style={styles.titleRow}>
        <Text style={[styles.title, variant === 'utility' && styles.titleUtility]}>{title || 'Outfit'}</Text>
        {!!badge && (
          <View style={[styles.badge, badge === 'PACK' && styles.badgePack]}>
            <Text style={[styles.badgeText, badge === 'PACK' && styles.badgeTextPack]}>{badge}</Text>
          </View>
        )}
      </View>

      {!!rationale && (
        <View style={[styles.rationalePill, variant === 'utility' && styles.rationalePillUtility]}>
          <Text style={[styles.rationalePillText, variant === 'utility' && styles.rationalePillTextUtility]}>
            {rationale}
          </Text>
        </View>
      )}

      {slots.map((slot) => {
        const thumb = slot.item ? mediaUrl(slot.item.thumbnail_url ?? slot.item.image_url) : undefined;
        const fallbackName = slot.label === 'Outerwear' ? 'Optional' : `No ${slot.label.toLowerCase()} yet`;
        const slotKey = SLOT_KEY[slot.label];
        const showSwap = !!slot.item && !!onSwapSlot;
        const isSwapping = swappingSlot === slotKey;
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
            {showSwap ? (
              <Pressable
                style={styles.swapBtn}
                onPress={() => onSwapSlot(slotKey)}
                disabled={!!swappingSlot}
              >
                {isSwapping ? (
                  <ActivityIndicator size="small" color={COLORS.primary} />
                ) : (
                  <Text style={styles.swapBtnText}>Swap</Text>
                )}
              </Pressable>
            ) : null}
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

      {hasOutfit && (onLike || onDislike) && (
        <View style={styles.feedbackRow}>
          {onLike ? (
            <Button
              title="👍 Like"
              variant="outline"
              loading={feedbackLoading}
              onPress={onLike}
              style={styles.feedbackBtn}
            />
          ) : null}
          {onDislike ? (
            <Button
              title="👎 Not for me"
              variant="secondary"
              loading={feedbackLoading}
              onPress={onDislike}
              style={styles.feedbackBtn}
            />
          ) : null}
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
    backgroundColor: THEME.editorial.surface,
    borderRadius: 20,
    padding: 18,
    ...SHADOW.soft,
    marginBottom: 16,
    marginTop: 12,
  },
  cardUtility: {
    backgroundColor: THEME.utility.surface,
    borderWidth: 0,
  },
  titleRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  title: { fontSize: 20, fontFamily: 'Georgia', fontWeight: '400', color: THEME.editorial.text, flex: 1 },
  titleUtility: utilityTitle(18),
  badge: {
    backgroundColor: THEME.editorial.text,
    borderRadius: 12,
    paddingHorizontal: 10,
    paddingVertical: 4,
    marginLeft: 8,
  },
  badgePack: { backgroundColor: THEME.editorial.pill },
  badgeText: { fontSize: 10, fontWeight: '800', color: '#fff', letterSpacing: 0.8 },
  badgeTextPack: { color: THEME.editorial.accentDark },
  rationalePill: {
    alignSelf: 'flex-start',
    backgroundColor: THEME.editorial.pill,
    borderRadius: 20,
    paddingHorizontal: 12,
    paddingVertical: 6,
    marginTop: 10,
    marginBottom: 6,
  },
  rationalePillUtility: { backgroundColor: THEME.editorial.pill },
  rationalePillText: { fontSize: 12, color: THEME.editorial.accentDark, fontWeight: '600' },
  rationalePillTextUtility: { color: THEME.editorial.accentDark },
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
    backgroundColor: THEME.editorial.pill,
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
  swapBtn: {
    paddingHorizontal: 10,
    paddingVertical: 8,
    borderRadius: 10,
    backgroundColor: THEME.editorial.pill,
    minWidth: 56,
    alignItems: 'center',
    justifyContent: 'center',
  },
  swapBtnText: { fontSize: 12, fontWeight: '700', color: THEME.brand.ink },
  packSection: {
    marginTop: 14,
    backgroundColor: THEME.utility.surfaceMuted,
    borderRadius: 12,
    padding: 12,
  },
  packHeading: { fontSize: 13, fontWeight: '800', color: THEME.brand.accent, marginBottom: 6 },
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
  feedbackRow: { flexDirection: 'row', gap: 10, marginTop: 14 },
  feedbackBtn: { flex: 1 },
  woreBtn: { marginTop: 12 },
});
