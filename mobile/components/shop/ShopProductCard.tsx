import React from 'react';
import { Image, Pressable, StyleSheet, Text, View } from 'react-native';

import { mediaUrl } from '../../constants/config';
import { THEME, FONTS, SHADOW } from '../../constants/theme';
import { ShopRecommendation } from '../../types';

const PRIORITY_LABEL: Record<string, string> = {
  high: 'Top pick',
  medium: 'Strong add',
  low: 'Worth a look',
};

type Props = {
  item: ShopRecommendation;
  onOpen: () => void;
  onPreviewOutfits: () => void;
};

function formatPrice(usd: number) {
  return `$${usd.toFixed(usd % 1 === 0 ? 0 : 2)}`;
}

export function ShopProductCard({ item, onOpen, onPreviewOutfits }: Props) {
  const priority = PRIORITY_LABEL[item.priority] ?? 'Pick';
  const hasPreviews = (item.sample_outfits?.length ?? 0) > 0;

  return (
    <View style={styles.card}>
      <Pressable onPress={onOpen}>
        <View style={styles.imageWrap}>
          {item.image_url ? (
            <Image source={{ uri: item.image_url }} style={styles.image} resizeMode="cover" />
          ) : (
            <View style={styles.placeholder}>
              <Text style={styles.placeholderEmoji}>🛍️</Text>
            </View>
          )}
          <View style={styles.priorityBadge}>
            <Text style={styles.priorityText}>{priority}</Text>
          </View>
        </View>
      </Pressable>

      <View style={styles.body}>
        <Text style={styles.retailer}>{item.retailer || item.brand}</Text>
        <Text style={styles.name}>{item.name}</Text>
        <Text style={styles.meta}>
          {item.category}
          {item.color ? ` · ${item.color}` : ''} · {formatPrice(item.price_usd)}
        </Text>

        <Pressable style={styles.outfitPill} onPress={onPreviewOutfits}>
          <Text style={styles.outfitPillText}>
            +{item.outfit_count} outfit{item.outfit_count === 1 ? '' : 's'} with your closet
          </Text>
          <Text style={styles.outfitPillHint}>{hasPreviews ? 'Tap to preview' : 'See combinations'}</Text>
        </Pressable>

        <Text style={styles.pitch}>{item.pitch}</Text>

        <Pressable style={styles.cta} onPress={onOpen}>
          <Text style={styles.ctaText}>View at {item.retailer || item.brand}</Text>
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: THEME.utility.surface,
    borderRadius: 20,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: THEME.utility.border,
    ...SHADOW.soft,
  },
  imageWrap: {
    width: '100%',
    aspectRatio: 4 / 5,
    backgroundColor: THEME.editorial.pill,
    position: 'relative',
  },
  image: { width: '100%', height: '100%' },
  placeholder: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  placeholderEmoji: { fontSize: 48 },
  priorityBadge: {
    position: 'absolute',
    top: 12,
    left: 12,
    backgroundColor: 'rgba(28, 28, 28, 0.78)',
    borderRadius: 12,
    paddingHorizontal: 10,
    paddingVertical: 5,
  },
  priorityText: {
    color: '#fff',
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.6,
    textTransform: 'uppercase',
  },
  body: { padding: 16, gap: 8 },
  retailer: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1,
    textTransform: 'uppercase',
    color: THEME.utility.textMuted,
  },
  name: {
    fontFamily: FONTS.sans,
    fontSize: 18,
    fontWeight: '700',
    color: THEME.utility.text,
    lineHeight: 23,
  },
  meta: {
    fontSize: 13,
    color: THEME.utility.textMuted,
    textTransform: 'capitalize',
  },
  outfitPill: {
    alignSelf: 'flex-start',
    backgroundColor: THEME.brand.ink,
    borderRadius: 14,
    paddingHorizontal: 12,
    paddingVertical: 8,
    marginTop: 4,
    gap: 2,
  },
  outfitPillText: { color: '#fff', fontSize: 12, fontWeight: '700' },
  outfitPillHint: { color: 'rgba(255,255,255,0.78)', fontSize: 10, fontWeight: '600' },
  pitch: {
    fontSize: 14,
    lineHeight: 20,
    color: THEME.utility.textMuted,
    marginTop: 4,
  },
  cta: {
    marginTop: 8,
    borderWidth: 1.5,
    borderColor: THEME.brand.ink,
    borderRadius: 14,
    paddingVertical: 12,
    alignItems: 'center',
  },
  ctaText: { fontSize: 14, fontWeight: '700', color: THEME.brand.ink },
});
