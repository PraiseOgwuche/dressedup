import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Image,
  Pressable,
  ActivityIndicator,
  ScrollView,
} from 'react-native';
import { THEME, FONTS, SHADOW } from '../constants/theme';
import { mediaUrl } from '../constants/config';
import { AVATAR_3D_ENABLED } from '../constants/avatar';
import { ClosetItem } from '../types';
import { Button } from './ui/Button';
import { OutfitSlotKey } from './OutfitCard';
import { OutfitLookBoard } from './OutfitLookBoard';
import { OutfitAvatarViewer } from './avatar/OutfitAvatarViewer';

interface OutfitHeroProps {
  top?: ClosetItem | null;
  bottom?: ClosetItem | null;
  shoes?: ClosetItem | null;
  outerwear?: ClosetItem | null;
  dress?: ClosetItem | null;
  bag?: ClosetItem | null;
  accessory?: ClosetItem | null;
  headwear?: ClosetItem | null;
  rationale?: string | null;
  stylingNote?: string | null;
  interpretation?: string | null;
  loading?: boolean;
  onShuffle?: () => void;
  onWore?: () => void;
  woreLoading?: boolean;
  onLike?: () => void;
  onDislike?: () => void;
  feedbackLoading?: boolean;
  onSwapSlot?: (slot: OutfitSlotKey) => void;
  swappingSlot?: OutfitSlotKey | null;
}

const SLOT_FALLBACK: Record<string, string> = {
  top: '#6B7686',
  bottom: '#3E4A5A',
  shoes: '#2A2E35',
  outerwear: '#54606E',
};

/** Named closet colors → hex when color_hex is missing. */
const NAMED_COLORS: Record<string, string> = {
  black: '#1A1A1A',
  white: '#F2F0EA',
  grey: '#8A8580',
  gray: '#8A8580',
  charcoal: '#3A3A3A',
  navy: '#1F2A44',
  blue: '#3B5BDB',
  red: '#B33A2B',
  rust: '#A14A32',
  orange: '#C56A2B',
  yellow: '#D4A017',
  green: '#3E6B4F',
  olive: '#6B6E3F',
  beige: '#C8B89A',
  tan: '#B8956A',
  brown: '#6B4A32',
  cream: '#F0E6D2',
  pink: '#D4899A',
  purple: '#6B4C7A',
  khaki: '#B5A67A',
};

function fabricColor(item?: ClosetItem | null, fallback = '#888888'): string {
  if (!item) return fallback;
  if (item.color_hex) return item.color_hex;
  const named = (item.color || '').toLowerCase().trim();
  return NAMED_COLORS[named] || fallback;
}

function pieceUri(item?: ClosetItem | null): string | null {
  if (!item) return null;
  return mediaUrl(item.thumbnail_url ?? item.image_url) || '';
}

export function OutfitHero({
  top,
  bottom,
  shoes,
  outerwear,
  dress,
  bag,
  accessory,
  headwear,
  rationale,
  stylingNote,
  interpretation,
  loading,
  onShuffle,
  onWore,
  woreLoading,
  onLike,
  onDislike,
  feedbackLoading,
  onSwapSlot,
  swappingSlot,
}: OutfitHeroProps) {
  const [avatarFailed, setAvatarFailed] = useState(false);
  const use3dAvatar = AVATAR_3D_ENABLED && !avatarFailed;

  const slots = dress
    ? [
        { key: 'dress' as const, label: 'Dress', item: dress },
        { key: 'shoes' as const, label: 'Shoes', item: shoes },
        { key: 'outerwear' as const, label: 'Layer', item: outerwear },
      ]
    : [
        { key: 'top' as const, label: 'Top', item: top },
        { key: 'bottom' as const, label: 'Bottom', item: bottom },
        { key: 'shoes' as const, label: 'Shoes', item: shoes },
        { key: 'outerwear' as const, label: 'Layer', item: outerwear },
      ];

  const finishing = [
    { key: 'bag', label: 'Bag', item: bag },
    { key: 'accessory', label: 'Accessory', item: accessory },
    { key: 'headwear', label: 'Headwear', item: headwear },
  ].filter((p) => p.item);

  const pieces = slots.filter((p) => p.item);
  const hasOutfit = pieces.length > 0;

  const renderGallery = (compact = false) => (
    <ScrollView
      horizontal
      showsHorizontalScrollIndicator={false}
      contentContainerStyle={[styles.gallery, compact && styles.galleryCompact]}
    >
      {pieces.map(({ key, label, item }) => {
        const uri = mediaUrl(item?.thumbnail_url ?? item?.image_url);
        const swapping = swappingSlot === key;
        return (
          <Pressable
            key={key}
            style={[styles.piece, compact && styles.pieceCompact]}
            onPress={onSwapSlot ? () => onSwapSlot(key) : undefined}
            disabled={!onSwapSlot || !!swappingSlot}
          >
            {uri ? (
              <Image
                source={{ uri }}
                style={[styles.pieceImage, compact && styles.pieceImageCompact]}
                resizeMode="cover"
              />
            ) : (
              <View style={[styles.piecePlaceholder, compact && styles.pieceImageCompact]}>
                <Text style={styles.pieceEmoji}>👕</Text>
              </View>
            )}
            <View style={styles.pieceFooter}>
              <Text style={styles.pieceLabel}>{label}</Text>
              <Text style={[styles.pieceName, compact && styles.pieceNameCompact]} numberOfLines={1}>
                {item?.name}
              </Text>
            </View>
            {onSwapSlot ? (
              <View style={styles.swapOverlay}>
                {swapping ? (
                  <ActivityIndicator color="#fff" size="small" />
                ) : (
                  <Text style={styles.swapText}>Swap</Text>
                )}
              </View>
            ) : null}
          </Pressable>
        );
      })}
    </ScrollView>
  );

  const styleNote = stylingNote || rationale;

  return (
    <View style={styles.wrap}>
      {interpretation ? (
        <Text style={styles.interpretation}>{interpretation}</Text>
      ) : null}

      {loading ? (
        <View style={styles.loadingBox}>
          <ActivityIndicator color={THEME.editorial.accentDark} size="large" />
          <Text style={styles.loadingText}>Curating your look…</Text>
        </View>
      ) : hasOutfit ? (
        <>
          {use3dAvatar ? (
            <>
              <OutfitAvatarViewer
                topUri={pieceUri(dress ?? top)}
                bottomUri={pieceUri(bottom)}
                shoesUri={pieceUri(shoes)}
                outerUri={pieceUri(outerwear)}
                topCategory={(dress ?? top)?.category}
                topSubcategory={(dress ?? top)?.subcategory}
                bottomSubcategory={bottom?.subcategory}
                shoesSubcategory={shoes?.subcategory}
                outerSubcategory={outerwear?.subcategory}
                topColor={fabricColor(dress ?? top, SLOT_FALLBACK.top)}
                bottomColor={fabricColor(bottom, SLOT_FALLBACK.bottom)}
                shoesColor={fabricColor(shoes, SLOT_FALLBACK.shoes)}
                outerColor={fabricColor(outerwear, SLOT_FALLBACK.outerwear)}
                onFailed={() => setAvatarFailed(true)}
              />
              {onSwapSlot ? (
                <>
                  <Text style={styles.swapHint}>Tap a piece to swap</Text>
                  {renderGallery(true)}
                </>
              ) : null}
            </>
          ) : (
            <OutfitLookBoard
              slots={slots}
              swappingSlot={swappingSlot}
              onSwapSlot={onSwapSlot}
            />
          )}
        </>
      ) : (
        <View style={styles.emptyHero}>
          <Text style={styles.emptyTitle}>Your look awaits</Text>
          <Text style={styles.emptySub}>Add closet items or tap shuffle below.</Text>
        </View>
      )}

      {finishing.length > 0 && !loading ? (
        <View style={styles.finishingRow}>
          {finishing.map(({ key, label, item }) => {
            const uri = mediaUrl(item?.thumbnail_url ?? item?.image_url);
            return (
              <View key={key} style={styles.finishingChip}>
                {uri ? (
                  <Image source={{ uri }} style={styles.finishingImage} resizeMode="cover" />
                ) : null}
                <View style={styles.finishingText}>
                  <Text style={styles.finishingLabel}>{label}</Text>
                  <Text style={styles.finishingName} numberOfLines={1}>
                    {item?.name}
                  </Text>
                </View>
              </View>
            );
          })}
        </View>
      ) : null}

      {!!styleNote && (
        <View style={styles.rationalePill}>
          <Text style={styles.rationale}>{styleNote}</Text>
        </View>
      )}

      <View style={styles.actions}>
        {onShuffle ? (
          <Button title="Shuffle" variant="editorial" loading={loading} onPress={onShuffle} style={styles.actionBtn} />
        ) : null}
        {hasOutfit && onWore ? (
          <Button
            title="I wore this"
            variant="editorialOutline"
            loading={woreLoading}
            onPress={onWore}
            style={styles.actionBtn}
          />
        ) : null}
        {hasOutfit && (onLike || onDislike) ? (
          <View style={styles.feedbackRow}>
            {onLike ? (
              <Pressable style={styles.iconBtn} onPress={onLike} disabled={feedbackLoading}>
                <Text style={styles.iconBtnText}>👍</Text>
              </Pressable>
            ) : null}
            {onDislike ? (
              <Pressable style={styles.iconBtn} onPress={onDislike} disabled={feedbackLoading}>
                <Text style={styles.iconBtnText}>👎</Text>
              </Pressable>
            ) : null}
          </View>
        ) : null}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { marginBottom: 8 },
  interpretation: {
    fontFamily: FONTS.sans,
    fontSize: 13,
    color: THEME.editorial.accentDark,
    fontWeight: '600',
    marginBottom: 14,
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  loadingBox: { alignItems: 'center', paddingVertical: 48 },
  loadingText: { marginTop: 12, fontSize: 14, color: THEME.editorial.textMuted },
  swapHint: {
    fontSize: 11,
    fontWeight: '600',
    color: THEME.editorial.textMuted,
    letterSpacing: 0.8,
    textTransform: 'uppercase',
    marginBottom: 8,
    marginTop: 4,
  },
  gallery: { gap: 14, paddingVertical: 4 },
  galleryCompact: { gap: 10, paddingVertical: 0 },
  piece: {
    width: 148,
    backgroundColor: THEME.editorial.surface,
    borderRadius: 16,
    overflow: 'hidden',
    ...SHADOW.lift,
  },
  pieceCompact: {
    width: 108,
    borderRadius: 12,
  },
  pieceImage: { width: '100%', height: 168 },
  pieceImageCompact: { height: 96 },
  piecePlaceholder: {
    width: '100%',
    height: 168,
    backgroundColor: THEME.editorial.pill,
    alignItems: 'center',
    justifyContent: 'center',
  },
  pieceEmoji: { fontSize: 40 },
  pieceFooter: { padding: 10 },
  pieceLabel: {
    fontSize: 10,
    fontWeight: '700',
    color: THEME.editorial.textMuted,
    letterSpacing: 1.2,
    textTransform: 'uppercase',
  },
  pieceName: { fontSize: 14, fontWeight: '600', color: THEME.editorial.text, marginTop: 2 },
  pieceNameCompact: { fontSize: 12 },
  swapOverlay: {
    position: 'absolute',
    top: 10,
    right: 10,
    backgroundColor: 'rgba(28, 28, 28, 0.72)',
    borderRadius: 14,
    paddingHorizontal: 10,
    paddingVertical: 5,
    minWidth: 52,
    alignItems: 'center',
  },
  swapText: { color: '#fff', fontSize: 11, fontWeight: '700' },
  finishingRow: { flexDirection: 'row', gap: 8, marginTop: 12 },
  finishingChip: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: THEME.editorial.surface,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: THEME.editorial.border,
    padding: 6,
  },
  finishingImage: { width: 36, height: 36, borderRadius: 8 },
  finishingText: { flex: 1 },
  finishingLabel: {
    fontSize: 9,
    fontWeight: '700',
    color: THEME.editorial.textMuted,
    letterSpacing: 1,
    textTransform: 'uppercase',
  },
  finishingName: { fontSize: 12, fontWeight: '600', color: THEME.editorial.text },
  rationalePill: {
    marginTop: 16,
    backgroundColor: THEME.editorial.pill,
    borderRadius: 16,
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderWidth: 1,
    borderColor: THEME.editorial.border,
  },
  rationale: {
    fontSize: 14,
    lineHeight: 21,
    color: THEME.editorial.textMuted,
    textAlign: 'center',
  },
  emptyHero: {
    backgroundColor: THEME.editorial.surface,
    borderRadius: 20,
    padding: 32,
    alignItems: 'center',
    ...SHADOW.soft,
  },
  emptyTitle: { fontSize: 20, fontWeight: '700', letterSpacing: -0.4, color: THEME.editorial.text },
  emptySub: { fontSize: 14, color: THEME.editorial.textMuted, marginTop: 8, textAlign: 'center' },
  actions: { flexDirection: 'row', alignItems: 'center', gap: 10, marginTop: 16 },
  actionBtn: { flex: 1 },
  feedbackRow: { flexDirection: 'row', gap: 8 },
  iconBtn: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: THEME.editorial.pill,
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconBtnText: { fontSize: 20 },
});
