import React from 'react';
import { Image, Pressable, StyleSheet, Text, View } from 'react-native';

import { THEME, FONTS, SHADOW } from '../../constants/theme';
import { ShopGapCard as ShopGapCardType } from '../../types';

type Props = {
  gap: ShopGapCardType | null;
  onPreview?: () => void;
};

function formatPrice(usd?: number | null) {
  if (usd == null) return '';
  return `$${usd.toFixed(usd % 1 === 0 ? 0 : 2)}`;
}

export function ShopGapCard({ gap, onPreview }: Props) {
  if (!gap) return null;

  const hasPick = Boolean(gap.product_name);

  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <View style={styles.headerText}>
          <Text style={styles.kicker}>Closet gap</Text>
          <Text style={styles.title}>{gap.title}</Text>
        </View>
        {gap.unlock_outfits > 0 ? (
          <View style={styles.unlockBadge}>
            <Text style={styles.unlockValue}>+{gap.unlock_outfits}</Text>
            <Text style={styles.unlockLabel}>outfits</Text>
          </View>
        ) : null}
      </View>

      <Text style={styles.reason}>{gap.reason}</Text>

      {hasPick ? (
        <Pressable style={styles.pickRow} onPress={onPreview} disabled={!onPreview}>
          {gap.image_url ? (
            <Image source={{ uri: gap.image_url }} style={styles.pickImage} resizeMode="cover" />
          ) : (
            <View style={[styles.pickImage, styles.pickPlaceholder]}>
              <Text>🛍️</Text>
            </View>
          )}
          <View style={styles.pickBody}>
            <Text style={styles.pickBrand}>{gap.product_brand}</Text>
            <Text style={styles.pickName} numberOfLines={2}>
              {gap.product_name}
            </Text>
            {gap.price_usd != null ? (
              <Text style={styles.pickPrice}>{formatPrice(gap.price_usd)}</Text>
            ) : null}
            {onPreview ? <Text style={styles.previewLink}>Preview outfits →</Text> : null}
          </View>
        </Pressable>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: THEME.brand.sand,
    borderRadius: 20,
    padding: 16,
    borderWidth: 1,
    borderColor: THEME.utility.border,
    gap: 12,
    ...SHADOW.soft,
  },
  header: { flexDirection: 'row', alignItems: 'flex-start', gap: 12 },
  headerText: { flex: 1, gap: 4 },
  kicker: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1,
    textTransform: 'uppercase',
    color: THEME.utility.textMuted,
  },
  title: {
    fontFamily: FONTS.sans,
    fontSize: 18,
    fontWeight: '700',
    color: THEME.utility.text,
    lineHeight: 23,
  },
  unlockBadge: {
    backgroundColor: THEME.brand.ink,
    borderRadius: 14,
    paddingHorizontal: 10,
    paddingVertical: 8,
    alignItems: 'center',
    minWidth: 64,
  },
  unlockValue: { color: '#fff', fontSize: 16, fontWeight: '800' },
  unlockLabel: {
    color: 'rgba(255,255,255,0.8)',
    fontSize: 9,
    fontWeight: '700',
    textTransform: 'uppercase',
  },
  reason: {
    fontSize: 14,
    lineHeight: 20,
    color: THEME.utility.text,
  },
  pickRow: {
    flexDirection: 'row',
    gap: 12,
    backgroundColor: THEME.utility.surface,
    borderRadius: 16,
    padding: 10,
    borderWidth: 1,
    borderColor: THEME.utility.border,
  },
  pickImage: {
    width: 72,
    height: 90,
    borderRadius: 12,
    backgroundColor: THEME.editorial.pill,
  },
  pickPlaceholder: { alignItems: 'center', justifyContent: 'center' },
  pickBody: { flex: 1, gap: 4, justifyContent: 'center' },
  pickBrand: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.8,
    textTransform: 'uppercase',
    color: THEME.utility.textMuted,
  },
  pickName: {
    fontSize: 14,
    fontWeight: '700',
    color: THEME.utility.text,
    lineHeight: 18,
  },
  pickPrice: { fontSize: 13, fontWeight: '600', color: THEME.utility.textMuted },
  previewLink: {
    marginTop: 4,
    fontSize: 12,
    fontWeight: '700',
    color: THEME.brand.ink,
  },
});
