import React, { useCallback, useEffect, useState } from 'react';
import {
  Alert,
  FlatList,
  Image,
  Linking,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useFocusEffect } from 'expo-router';

import { THEME, SHADOW, utilityTitle } from '../../constants/theme';
import { shopAPI } from '../../services/api';
import { ShopRecommendation } from '../../types';
import { ChipSelect } from '../../components/ui/ChipSelect';

const CATEGORY_FILTERS = [
  { label: 'All', value: '' },
  { label: 'Tops', value: 'top' },
  { label: 'Bottoms', value: 'bottom' },
  { label: 'Shoes', value: 'footwear' },
  { label: 'Outerwear', value: 'outerwear' },
];

function formatPrice(usd: number) {
  return `$${usd.toFixed(usd % 1 === 0 ? 0 : 2)}`;
}

export default function ShopScreen() {
  const [summary, setSummary] = useState('');
  const [recommendations, setRecommendations] = useState<ShopRecommendation[]>([]);
  const [category, setCategory] = useState('');
  const [loading, setLoading] = useState(false);

  const loadRecommendations = useCallback(async () => {
    setLoading(true);
    try {
      const response = await shopAPI.getRecommendations(category || undefined);
      setSummary(response.summary);
      setRecommendations(response.recommendations);
    } catch {
      Alert.alert('Error', 'Could not load shop picks.');
    } finally {
      setLoading(false);
    }
  }, [category]);

  useFocusEffect(
    useCallback(() => {
      loadRecommendations();
    }, [loadRecommendations]),
  );

  useEffect(() => {
    loadRecommendations();
  }, [category]);

  const openProduct = async (url: string) => {
    if (!url) return;
    const can = await Linking.canOpenURL(url);
    if (can) {
      await Linking.openURL(url);
    } else {
      Alert.alert('Link unavailable', 'Could not open this product page.');
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Shop</Text>
        <Text style={styles.subtitle}>Curated picks that multiply your closet</Text>
      </View>
      <FlatList
        data={recommendations}
        keyExtractor={(item) => item.product_id}
        onRefresh={loadRecommendations}
        refreshing={loading}
        contentContainerStyle={recommendations.length ? styles.list : styles.emptyList}
        ListHeaderComponent={
          <View style={styles.listHeader}>
            {summary ? <Text style={styles.summary}>{summary}</Text> : null}
            <ChipSelect
              label="Category"
              options={CATEGORY_FILTERS.map((f) => f.label)}
              selected={CATEGORY_FILTERS.find((f) => f.value === category)?.label ?? 'All'}
              onSelect={(label) => {
                const next = CATEGORY_FILTERS.find((f) => f.label === label)?.value ?? '';
                setCategory(next);
              }}
            />
          </View>
        }
        ListEmptyComponent={
          <Text style={styles.emptyText}>
            {loading ? 'Finding picks for your closet…' : summary || 'Add more closet pieces to unlock recommendations.'}
          </Text>
        }
        renderItem={({ item }) => (
          <View style={styles.card}>
            <View style={styles.cardTop}>
              {item.image_url ? (
                <Image source={{ uri: item.image_url }} style={styles.productImage} resizeMode="cover" />
              ) : (
                <View style={[styles.swatch, { backgroundColor: THEME.editorial.pill }]}>
                  <View style={[styles.swatchFill, { backgroundColor: swatchColor(item) }]} />
                </View>
              )}
              <View style={styles.cardBody}>
                <Text style={styles.retailer}>{item.retailer || item.brand}</Text>
                <Text style={styles.brand}>{item.brand}</Text>
                <Text style={styles.name}>{item.name}</Text>
                <Text style={styles.meta}>
                  {item.category}
                  {item.color ? ` · ${item.color}` : ''}
                  {' · '}
                  {formatPrice(item.price_usd)}
                </Text>
              </View>
            </View>
            <View style={styles.outfitBadge}>
              <Text style={styles.outfitBadgeText}>
                ~{item.outfit_count} outfit{item.outfit_count === 1 ? '' : 's'} with your closet
              </Text>
            </View>
            <Text style={styles.reason}>{item.pitch}</Text>
            <Pressable style={styles.shopBtn} onPress={() => openProduct(item.buy_url || item.product_url)}>
              <Text style={styles.shopBtnText}>Shop at {item.retailer || item.brand}</Text>
            </Pressable>
          </View>
        )}
      />
    </SafeAreaView>
  );
}

function swatchColor(item: ShopRecommendation): string {
  const map: Record<string, string> = {
    white: '#F4F1EA',
    navy: '#1E2A44',
    indigo: '#2C3E5C',
    charcoal: '#3D3D3D',
    grey: '#9A9A9A',
    gray: '#9A9A9A',
    tan: '#C4A574',
    black: '#1C1C1C',
    camel: '#C9A66B',
    brown: '#8B6914',
  };
  return map[item.color?.toLowerCase() ?? ''] ?? THEME.editorial.pill;
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: THEME.utility.background,
  },
  header: {
    paddingHorizontal: 22,
    paddingTop: 12,
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: THEME.utility.border,
  },
  title: {
    ...utilityTitle(28),
    textAlign: 'left',
  },
  subtitle: {
    marginTop: 6,
    fontSize: 14,
    color: THEME.utility.textMuted,
    lineHeight: 20,
  },
  list: {
    padding: 22,
    gap: 14,
    paddingBottom: 40,
  },
  listHeader: {
    gap: 12,
    marginBottom: 16,
  },
  emptyList: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: 22,
  },
  summary: {
    fontSize: 15,
    lineHeight: 22,
    color: THEME.utility.text,
    fontWeight: '600',
  },
  emptyText: {
    fontSize: 16,
    color: THEME.utility.textMuted,
    textAlign: 'center',
    lineHeight: 22,
  },
  card: {
    backgroundColor: THEME.utility.surface,
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: THEME.utility.border,
    ...SHADOW.soft,
  },
  cardTop: {
    flexDirection: 'row',
    gap: 14,
  },
  productImage: {
    width: 88,
    height: 88,
    borderRadius: 12,
    backgroundColor: THEME.editorial.pill,
  },
  swatch: {
    width: 88,
    height: 88,
    borderRadius: 12,
    overflow: 'hidden',
    backgroundColor: THEME.editorial.pill,
  },
  swatchFill: {
    flex: 1,
  },
  cardBody: {
    flex: 1,
  },
  retailer: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1,
    textTransform: 'uppercase',
    color: THEME.utility.textMuted,
  },
  brand: {
    marginTop: 2,
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 1.2,
    textTransform: 'uppercase',
    color: THEME.editorial.accentDark,
  },
  name: {
    marginTop: 4,
    fontSize: 17,
    fontWeight: '700',
    color: THEME.utility.text,
    lineHeight: 22,
  },
  meta: {
    marginTop: 4,
    fontSize: 12,
    color: THEME.utility.textMuted,
    textTransform: 'capitalize',
  },
  outfitBadge: {
    marginTop: 14,
    alignSelf: 'flex-start',
    backgroundColor: THEME.brand.ink,
    borderRadius: 20,
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  outfitBadgeText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '700',
  },
  reason: {
    marginTop: 12,
    fontSize: 14,
    lineHeight: 20,
    color: THEME.utility.textMuted,
  },
  shopBtn: {
    marginTop: 14,
    borderWidth: 1.5,
    borderColor: THEME.brand.ink,
    borderRadius: 12,
    paddingVertical: 12,
    alignItems: 'center',
  },
  shopBtnText: {
    fontSize: 15,
    fontWeight: '700',
    color: THEME.brand.ink,
  },
});
