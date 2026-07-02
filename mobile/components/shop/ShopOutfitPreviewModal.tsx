import React, { useMemo, useState } from 'react';
import {
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { OutfitLookBoard } from '../OutfitLookBoard';
import { THEME, FONTS } from '../../constants/theme';
import { openExternalUrl } from '../../services/openUrl';
import { ClosetItem, ShopOutfitPreview, ShopRecommendation } from '../../types';

type Props = {
  product: ShopRecommendation | null;
  visible: boolean;
  onClose: () => void;
};

function toClosetItem(garment: ShopOutfitPreview['top']): ClosetItem | null {
  if (!garment) return null;
  return {
    id: garment.id,
    user_id: 0,
    name: garment.name,
    category: garment.category,
    color: garment.color ?? undefined,
    image_url: garment.image_url ?? undefined,
    thumbnail_url: garment.thumbnail_url ?? garment.image_url ?? undefined,
    is_clean: true,
    times_worn: 0,
    wears_since_wash: 0,
    source: garment.is_shop_pick ? 'shop_catalog' : 'closet',
    needs_review: false,
    created_at: '',
  };
}

export function ShopOutfitPreviewModal({ product, visible, onClose }: Props) {
  const outfits = product?.sample_outfits ?? [];
  const [index, setIndex] = useState(0);

  const active = outfits[index];

  const slots = useMemo(() => {
    if (!active) return [];
    return [
      { key: 'top' as const, label: active.top?.is_shop_pick ? 'Shop pick' : 'Top', item: toClosetItem(active.top) },
      { key: 'bottom' as const, label: active.bottom?.is_shop_pick ? 'Shop pick' : 'Bottom', item: toClosetItem(active.bottom) },
      { key: 'shoes' as const, label: active.shoes?.is_shop_pick ? 'Shop pick' : 'Shoes', item: toClosetItem(active.shoes) },
      ...(active.outerwear
        ? [{ key: 'outerwear' as const, label: 'Shop pick', item: toClosetItem(active.outerwear) }]
        : []),
    ];
  }, [active]);

  if (!product) return null;

  return (
    <Modal visible={visible} animationType="slide" presentationStyle="pageSheet" onRequestClose={onClose}>
      <View style={styles.container}>
        <View style={styles.header}>
          <View style={styles.headerText}>
            <Text style={styles.kicker}>Outfits with your closet</Text>
            <Text style={styles.title}>{product.brand} {product.name}</Text>
            <Text style={styles.meta}>
              {product.outfit_count} possible outfit{product.outfit_count === 1 ? '' : 's'} · showing top{' '}
              {Math.min(outfits.length, 3)}
            </Text>
          </View>
          <Pressable onPress={onClose} hitSlop={12}>
            <Text style={styles.close}>Done</Text>
          </Pressable>
        </View>

        {outfits.length === 0 ? (
          <View style={styles.empty}>
            <Text style={styles.emptyText}>
              We counted {product.outfit_count} combinations — preview samples will appear after you refresh picks.
            </Text>
          </View>
        ) : (
          <ScrollView contentContainerStyle={styles.body}>
            <OutfitLookBoard slots={slots} compact />

            {outfits.length > 1 ? (
              <View style={styles.dots}>
                {outfits.map((outfit, i) => (
                  <Pressable
                    key={`${outfit.score}-${i}`}
                    style={[styles.dot, i === index && styles.dotActive]}
                    onPress={() => setIndex(i)}
                  />
                ))}
              </View>
            ) : null}

            <Text style={styles.caption}>
              Sample {index + 1} · match score {Math.round((active?.score ?? 0) * 100)}%
            </Text>
            <Text style={styles.hint}>
              Highlighted slots marked “Shop pick” are this product paired with pieces you already own.
            </Text>
          </ScrollView>
        )}

        <View style={styles.footer}>
          <Pressable
            style={styles.buyBtn}
            onPress={() => openExternalUrl(product.buy_url || product.product_url)}
          >
            <Text style={styles.buyBtnText}>View at {product.retailer || product.brand}</Text>
          </Pressable>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: THEME.utility.background },
  header: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    paddingHorizontal: 22,
    paddingTop: 20,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: THEME.utility.border,
    gap: 12,
  },
  headerText: { flex: 1, gap: 4 },
  kicker: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 1,
    textTransform: 'uppercase',
    color: THEME.utility.textMuted,
  },
  title: {
    fontFamily: FONTS.sans,
    fontSize: 20,
    fontWeight: '700',
    color: THEME.utility.text,
    lineHeight: 26,
  },
  meta: { fontSize: 13, color: THEME.utility.textMuted },
  close: { fontSize: 16, fontWeight: '700', color: THEME.brand.ink },
  body: { padding: 22, gap: 14, paddingBottom: 40 },
  empty: { flex: 1, padding: 22, justifyContent: 'center' },
  emptyText: { fontSize: 15, lineHeight: 22, color: THEME.utility.textMuted, textAlign: 'center' },
  dots: { flexDirection: 'row', justifyContent: 'center', gap: 8, marginTop: 4 },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: THEME.utility.border,
  },
  dotActive: { backgroundColor: THEME.brand.ink, width: 22 },
  caption: { fontSize: 14, fontWeight: '700', color: THEME.utility.text, textAlign: 'center' },
  hint: { fontSize: 13, lineHeight: 19, color: THEME.utility.textMuted, textAlign: 'center' },
  footer: {
    paddingHorizontal: 22,
    paddingBottom: 28,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: THEME.utility.border,
  },
  buyBtn: {
    backgroundColor: THEME.brand.ink,
    borderRadius: 14,
    paddingVertical: 14,
    alignItems: 'center',
  },
  buyBtnText: { color: '#fff', fontSize: 15, fontWeight: '700' },
});
