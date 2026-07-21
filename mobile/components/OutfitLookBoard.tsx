import React from 'react';
import {
  ActivityIndicator,
  Image,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { mediaUrl } from '../constants/config';
import { THEME, FONTS, SHADOW } from '../constants/theme';
import { ClosetItem } from '../types';
import { OutfitSlotKey } from './OutfitCard';

type Slot = {
  key: OutfitSlotKey;
  label: string;
  item?: ClosetItem | null;
};

type Props = {
  slots: Slot[];
  swappingSlot?: OutfitSlotKey | null;
  onSwapSlot?: (slot: OutfitSlotKey) => void;
  compact?: boolean;
};

const SLOT_EMOJI: Record<string, string> = {
  top: '👕',
  bottom: '👖',
  shoes: '👟',
  outerwear: '🧥',
  dress: '👗',
};

function SlotTile({
  slot,
  style,
  imageStyle,
  swapping,
  onPress,
}: {
  slot: Slot;
  style?: object;
  imageStyle?: object;
  swapping?: boolean;
  onPress?: () => void;
}) {
  const uri = slot.item ? mediaUrl(slot.item.thumbnail_url ?? slot.item.image_url) : undefined;
  const empty = !slot.item;

  return (
    <Pressable
      style={[styles.tile, empty && styles.tileEmpty, style]}
      onPress={onPress}
      disabled={!onPress || swapping}
    >
      {uri ? (
        <Image source={{ uri }} style={[styles.tileImage, imageStyle]} resizeMode="cover" />
      ) : (
        <View style={[styles.tilePlaceholder, imageStyle]}>
          <Text style={styles.tileEmoji}>{SLOT_EMOJI[slot.key] ?? '✨'}</Text>
        </View>
      )}
      <View style={styles.tileLabel}>
        <Text style={styles.tileLabelText}>{slot.label}</Text>
        {slot.item ? (
          <Text style={styles.tileName} numberOfLines={1}>
            {slot.item.name}
          </Text>
        ) : (
          <Text style={styles.tileEmptyHint}>Tap to add</Text>
        )}
      </View>
      {onPress ? (
        <View style={styles.swapBadge}>
          {swapping ? (
            <ActivityIndicator color="#fff" size="small" />
          ) : (
            <Text style={styles.swapBadgeText}>{empty ? 'Add' : 'Swap'}</Text>
          )}
        </View>
      ) : null}
    </Pressable>
  );
}

/**
 * Magazine-style flat-lay board for today's outfit — photo-first, tap slots to swap.
 */
export function OutfitLookBoard({ slots, swappingSlot, onSwapSlot, compact }: Props) {
  const top = slots.find((s) => s.key === 'top') ?? { key: 'top' as const, label: 'Top', item: null };
  const bottom = slots.find((s) => s.key === 'bottom') ?? { key: 'bottom' as const, label: 'Bottom', item: null };
  const shoes = slots.find((s) => s.key === 'shoes') ?? { key: 'shoes' as const, label: 'Shoes', item: null };
  const outer = slots.find((s) => s.key === 'outerwear');
  const dress = slots.find((s) => s.key === 'dress');

  const swap = (key: OutfitSlotKey) => (onSwapSlot ? () => onSwapSlot(key) : undefined);

  return (
    <View style={[styles.board, compact && styles.boardCompact]}>
      <View style={[styles.mainRow, compact && styles.mainRowCompact]}>
        {dress?.item ? (
          // A dress covers top+bottom: hero tile is the dress, shoes beside it.
          <>
            <SlotTile
              slot={dress}
              style={styles.topTile}
              imageStyle={[styles.topImage, compact && styles.topImageCompact]}
              swapping={swappingSlot === 'dress'}
              onPress={swap('dress')}
            />
            <View style={styles.sideStack}>
              <SlotTile
                slot={shoes}
                style={styles.sideTile}
                imageStyle={[styles.sideImage, compact && styles.sideImageCompact]}
                swapping={swappingSlot === 'shoes'}
                onPress={swap('shoes')}
              />
            </View>
          </>
        ) : (
          <>
            <SlotTile
              slot={top}
              style={styles.topTile}
              imageStyle={[styles.topImage, compact && styles.topImageCompact]}
              swapping={swappingSlot === 'top'}
              onPress={swap('top')}
            />
            <View style={styles.sideStack}>
              <SlotTile
                slot={bottom}
                style={styles.sideTile}
                imageStyle={[styles.sideImage, compact && styles.sideImageCompact]}
                swapping={swappingSlot === 'bottom'}
                onPress={swap('bottom')}
              />
              <SlotTile
                slot={shoes}
                style={styles.sideTile}
                imageStyle={[styles.sideImage, compact && styles.sideImageCompact]}
                swapping={swappingSlot === 'shoes'}
                onPress={swap('shoes')}
              />
            </View>
          </>
        )}
      </View>
      {outer?.item || onSwapSlot ? (
        <SlotTile
          slot={outer ?? { key: 'outerwear', label: 'Layer', item: null }}
          style={styles.outerTile}
          imageStyle={[styles.outerImage, compact && styles.outerImageCompact]}
          swapping={swappingSlot === 'outerwear'}
          onPress={swap('outerwear')}
        />
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  board: {
    backgroundColor: THEME.editorial.surface,
    borderRadius: 22,
    padding: 10,
    borderWidth: 1,
    borderColor: THEME.editorial.border,
    ...SHADOW.lift,
  },
  boardCompact: {
    borderRadius: 16,
    padding: 8,
  },
  mainRow: {
    flexDirection: 'row',
    gap: 10,
    minHeight: 260,
  },
  mainRowCompact: {
    minHeight: 190,
  },
  topTile: { flex: 1.15 },
  topImage: { flex: 1, minHeight: 240, borderRadius: 16 },
  topImageCompact: { minHeight: 176, borderRadius: 12 },
  sideStack: { flex: 1, gap: 10 },
  sideTile: { flex: 1 },
  sideImage: { flex: 1, minHeight: 115, borderRadius: 14 },
  sideImageCompact: { minHeight: 82, borderRadius: 10 },
  outerTile: { marginTop: 10 },
  outerImage: { height: 88, borderRadius: 14 },
  outerImageCompact: { height: 64, borderRadius: 10 },
  tile: {
    borderRadius: 16,
    overflow: 'hidden',
    backgroundColor: THEME.editorial.pill,
    position: 'relative',
  },
  tileEmpty: { opacity: 0.72 },
  tileImage: { width: '100%' },
  tilePlaceholder: {
    width: '100%',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: THEME.editorial.pill,
  },
  tileEmoji: { fontSize: 36 },
  tileLabel: {
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 0,
    paddingHorizontal: 10,
    paddingVertical: 8,
    backgroundColor: 'rgba(28, 28, 28, 0.45)',
  },
  tileLabelText: {
    fontSize: 9,
    fontWeight: '700',
    color: 'rgba(255,255,255,0.85)',
    letterSpacing: 1.1,
    textTransform: 'uppercase',
  },
  tileName: {
    fontFamily: FONTS.sans,
    fontSize: 12,
    fontWeight: '700',
    color: '#fff',
    marginTop: 2,
  },
  tileEmptyHint: {
    fontSize: 11,
    color: 'rgba(255,255,255,0.75)',
    marginTop: 2,
    fontStyle: 'italic',
  },
  swapBadge: {
    position: 'absolute',
    top: 10,
    right: 10,
    backgroundColor: 'rgba(28, 28, 28, 0.72)',
    borderRadius: 12,
    paddingHorizontal: 10,
    paddingVertical: 5,
    minWidth: 52,
    alignItems: 'center',
  },
  swapBadgeText: { color: '#fff', fontSize: 10, fontWeight: '700' },
});
