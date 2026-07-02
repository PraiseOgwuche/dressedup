import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Alert,
  FlatList,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useFocusEffect } from 'expo-router';

import { THEME, FONTS, SHADOW, utilityTitle } from '../../constants/theme';
import { marketplaceAPI, shopAPI, styleAPI } from '../../services/api';
import { getApiErrorMessage } from '../../services/errors';
import { ClosetListing, ListingType, ShopRecommendation } from '../../types';
import { ShopProductCard } from '../../components/shop/ShopProductCard';
import { ShopOutfitPreviewModal } from '../../components/shop/ShopOutfitPreviewModal';
import { MarketplaceListingCard } from '../../components/shop/MarketplaceListingCard';
import { CreateListingModal } from '../../components/shop/CreateListingModal';
import { Button } from '../../components/ui/Button';
import { openExternalUrl } from '../../services/openUrl';

type ShopSection = 'picks' | 'passiton';
type PassMode = 'browse' | 'mine';

const PICK_CATEGORIES = [
  { label: 'All', value: '' },
  { label: 'Tops', value: 'top' },
  { label: 'Bottoms', value: 'bottom' },
  { label: 'Shoes', value: 'footwear' },
  { label: 'Layers', value: 'outerwear' },
];

const PASS_FILTERS: { label: string; value: ListingType | '' }[] = [
  { label: 'All', value: '' },
  { label: 'For sale', value: 'sell' },
  { label: 'Free gifts', value: 'gift' },
];

export default function ShopScreen() {
  const [section, setSection] = useState<ShopSection>('picks');
  const [passMode, setPassMode] = useState<PassMode>('browse');

  const [summary, setSummary] = useState('');
  const [recommendations, setRecommendations] = useState<ShopRecommendation[]>([]);
  const [pickCategory, setPickCategory] = useState('');
  const [pickLoading, setPickLoading] = useState(false);

  const [listings, setListings] = useState<ClosetListing[]>([]);
  const [myListings, setMyListings] = useState<ClosetListing[]>([]);
  const [passFilter, setPassFilter] = useState<ListingType | ''>('');
  const [search, setSearch] = useState('');
  const [passLoading, setPassLoading] = useState(false);
  const [listModalOpen, setListModalOpen] = useState(false);
  const [previewProduct, setPreviewProduct] = useState<ShopRecommendation | null>(null);

  const listedItemIds = useMemo(
    () =>
      myListings.filter((l) => l.status === 'active').map((l) => l.item.id),
    [myListings],
  );

  const outfitPotential = useMemo(
    () => recommendations.reduce((sum, rec) => sum + rec.outfit_count, 0),
    [recommendations],
  );

  const loadPicks = useCallback(async () => {
    setPickLoading(true);
    try {
      const response = await shopAPI.getRecommendations(pickCategory || undefined);
      setSummary(response.summary);
      setRecommendations(response.recommendations);
    } catch (error) {
      Alert.alert('Error', getApiErrorMessage(error, 'Could not load shop picks.'));
    } finally {
      setPickLoading(false);
    }
  }, [pickCategory]);

  const loadPassItOn = useCallback(async () => {
    setPassLoading(true);
    try {
      const [browse, mine] = await Promise.all([
        marketplaceAPI.browse({
          listing_type: passFilter || undefined,
          q: search.trim() || undefined,
        }),
        marketplaceAPI.mine(),
      ]);
      setListings(browse);
      setMyListings(mine);
    } catch (error) {
      Alert.alert('Error', getApiErrorMessage(error, 'Could not load listings.'));
    } finally {
      setPassLoading(false);
    }
  }, [passFilter, search]);

  useFocusEffect(
    useCallback(() => {
      if (section === 'picks') loadPicks();
      else loadPassItOn();
    }, [section, loadPicks, loadPassItOn]),
  );

  useEffect(() => {
    if (section === 'picks') loadPicks();
  }, [pickCategory, loadPicks, section]);

  useEffect(() => {
    if (section === 'passiton') loadPassItOn();
  }, [passFilter, search, section, loadPassItOn]);

  const trackStyle = useCallback((payload: Parameters<typeof styleAPI.track>[0]) => {
    void styleAPI.track(payload).catch(() => {
      // non-blocking personalization signal
    });
  }, []);

  const openProduct = useCallback(
    (item: ShopRecommendation) => {
      trackStyle({ event_type: 'shop_tap', product_id: item.product_id });
      void openExternalUrl(item.buy_url || item.product_url);
    },
    [trackStyle],
  );

  const previewOutfits = useCallback(
    (item: ShopRecommendation) => {
      trackStyle({ event_type: 'shop_preview', product_id: item.product_id });
      setPreviewProduct(item);
    },
    [trackStyle],
  );

  const renderPicks = () => (
    <FlatList
      data={recommendations}
      keyExtractor={(item) => item.product_id}
      onRefresh={loadPicks}
      refreshing={pickLoading}
      contentContainerStyle={recommendations.length ? styles.list : styles.emptyList}
      ListHeaderComponent={
        <View style={styles.listHeader}>
          {summary ? <Text style={styles.summary}>{summary}</Text> : null}
          {recommendations.length > 0 ? (
            <View style={styles.statsRow}>
              <View style={styles.statPill}>
                <Text style={styles.statValue}>{recommendations.length}</Text>
                <Text style={styles.statLabel}>Picks</Text>
              </View>
              <View style={styles.statPill}>
                <Text style={styles.statValue}>+{outfitPotential}</Text>
                <Text style={styles.statLabel}>Outfits</Text>
              </View>
            </View>
          ) : null}
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.chips}>
            {PICK_CATEGORIES.map(({ label, value }) => {
              const active = pickCategory === value;
              return (
                <Pressable
                  key={label}
                  style={[styles.chip, active && styles.chipActive]}
                  onPress={() => setPickCategory(value)}
                >
                  <Text style={[styles.chipText, active && styles.chipTextActive]}>{label}</Text>
                </Pressable>
              );
            })}
          </ScrollView>
        </View>
      }
      ListEmptyComponent={
        !pickLoading ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyEmoji}>🛍️</Text>
            <Text style={styles.emptyTitle}>Build your closet first</Text>
            <Text style={styles.emptyBody}>
              Add a few tops and bottoms — we score curated picks by how many new outfits they unlock.
            </Text>
          </View>
        ) : null
      }
      renderItem={({ item }) => (
        <ShopProductCard
          item={item}
          onOpen={() => openProduct(item)}
          onPreviewOutfits={() => previewOutfits(item)}
        />
      )}
      ItemSeparatorComponent={() => <View style={styles.separator} />}
    />
  );

  const renderPassItOn = () => {
    const data = passMode === 'mine' ? myListings.filter((l) => l.status === 'active') : listings;

    return (
      <>
        <View style={styles.passToolbar}>
          <View style={styles.passModeRow}>
            {(['browse', 'mine'] as PassMode[]).map((mode) => (
              <Pressable
                key={mode}
                style={[styles.passModePill, passMode === mode && styles.passModePillActive]}
                onPress={() => setPassMode(mode)}
              >
                <Text style={[styles.passModeText, passMode === mode && styles.passModeTextActive]}>
                  {mode === 'browse' ? 'Browse' : 'My listings'}
                </Text>
              </Pressable>
            ))}
            <Pressable style={styles.listBtn} onPress={() => setListModalOpen(true)}>
              <Text style={styles.listBtnText}>+ List</Text>
            </Pressable>
          </View>

          {passMode === 'browse' ? (
            <>
              <TextInput
                style={styles.searchInput}
                placeholder="Search listings…"
                placeholderTextColor={THEME.utility.textMuted}
                value={search}
                onChangeText={setSearch}
                clearButtonMode="while-editing"
              />
              <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.chips}>
                {PASS_FILTERS.map(({ label, value }) => {
                  const active = passFilter === value;
                  return (
                    <Pressable
                      key={label}
                      style={[styles.chip, active && styles.chipActive]}
                      onPress={() => setPassFilter(value)}
                    >
                      <Text style={[styles.chipText, active && styles.chipTextActive]}>{label}</Text>
                    </Pressable>
                  );
                })}
              </ScrollView>
            </>
          ) : null}
        </View>

        <FlatList
          data={data}
          keyExtractor={(item) => item.id.toString()}
          numColumns={2}
          columnWrapperStyle={data.length ? styles.gridRow : undefined}
          onRefresh={loadPassItOn}
          refreshing={passLoading}
          contentContainerStyle={data.length ? styles.gridList : styles.emptyList}
          ListEmptyComponent={
            !passLoading ? (
              <View style={styles.emptyState}>
                <Text style={styles.emptyEmoji}>♻️</Text>
                <Text style={styles.emptyTitle}>
                  {passMode === 'mine' ? 'Nothing listed yet' : 'No listings yet'}
                </Text>
                <Text style={styles.emptyBody}>
                  {passMode === 'mine'
                    ? 'List pieces you want to sell or gift. Others contact you by email.'
                    : 'Be the first to pass something on — or check back as the community grows.'}
                </Text>
                <Button title="List from closet" onPress={() => setListModalOpen(true)} />
              </View>
            ) : null
          }
          renderItem={({ item }) => (
            <View style={styles.gridCell}>
              <MarketplaceListingCard listing={item} onChanged={loadPassItOn} />
            </View>
          )}
        />
      </>
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Shop</Text>
        <Text style={styles.subtitle}>Complete your closet — or pass pieces on to someone else.</Text>

        <View style={styles.sectionRow}>
          <Pressable
            style={[styles.sectionPill, section === 'picks' && styles.sectionPillActive]}
            onPress={() => setSection('picks')}
          >
            <Text style={[styles.sectionText, section === 'picks' && styles.sectionTextActive]}>
              New picks
            </Text>
          </Pressable>
          <Pressable
            style={[styles.sectionPill, section === 'passiton' && styles.sectionPillActive]}
            onPress={() => setSection('passiton')}
          >
            <Text style={[styles.sectionText, section === 'passiton' && styles.sectionTextActive]}>
              Pass it on
            </Text>
          </Pressable>
        </View>
      </View>

      {section === 'picks' ? renderPicks() : renderPassItOn()}

      <CreateListingModal
        visible={listModalOpen}
        listedItemIds={listedItemIds}
        onClose={() => setListModalOpen(false)}
        onCreated={loadPassItOn}
      />

      <ShopOutfitPreviewModal
        product={previewProduct}
        visible={previewProduct != null}
        onClose={() => setPreviewProduct(null)}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: THEME.utility.background },
  header: {
    paddingHorizontal: 22,
    paddingTop: 12,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: THEME.utility.border,
    gap: 8,
  },
  title: { ...utilityTitle(28), textAlign: 'left' },
  subtitle: { fontSize: 14, color: THEME.utility.textMuted, lineHeight: 20 },
  sectionRow: { flexDirection: 'row', gap: 8, marginTop: 4 },
  sectionPill: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 14,
    alignItems: 'center',
    backgroundColor: THEME.utility.surfaceMuted,
    borderWidth: 1,
    borderColor: THEME.utility.border,
  },
  sectionPillActive: { backgroundColor: THEME.brand.ink, borderColor: THEME.brand.ink },
  sectionText: { fontSize: 13, fontWeight: '700', color: THEME.utility.text },
  sectionTextActive: { color: '#fff' },
  list: { paddingHorizontal: 22, paddingTop: 16, paddingBottom: 40, gap: 14 },
  listHeader: { gap: 12, marginBottom: 8 },
  summary: { fontSize: 15, lineHeight: 22, color: THEME.utility.text, fontWeight: '600' },
  statsRow: { flexDirection: 'row', gap: 10 },
  statPill: {
    flex: 1,
    backgroundColor: THEME.utility.surface,
    borderRadius: 14,
    paddingVertical: 10,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: THEME.utility.border,
  },
  statValue: { fontSize: 18, fontWeight: '800', color: THEME.utility.text },
  statLabel: {
    marginTop: 2,
    fontSize: 11,
    fontWeight: '600',
    color: THEME.utility.textMuted,
    textTransform: 'uppercase',
  },
  chips: { gap: 8, paddingBottom: 4 },
  chip: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: THEME.utility.surface,
    borderWidth: 1,
    borderColor: THEME.utility.border,
  },
  chipActive: { backgroundColor: THEME.brand.ink, borderColor: THEME.brand.ink },
  chipText: { fontSize: 13, color: THEME.utility.text },
  chipTextActive: { color: '#fff', fontWeight: '700' },
  separator: { height: 14 },
  emptyList: { flexGrow: 1, paddingHorizontal: 22, paddingBottom: 40 },
  emptyState: {
    alignItems: 'center',
    backgroundColor: THEME.utility.surfaceMuted,
    borderRadius: 20,
    padding: 28,
    gap: 10,
    marginTop: 8,
    ...SHADOW.soft,
  },
  emptyEmoji: { fontSize: 48 },
  emptyTitle: {
    fontFamily: FONTS.sans,
    fontSize: 18,
    fontWeight: '700',
    color: THEME.utility.text,
    textAlign: 'center',
  },
  emptyBody: {
    fontSize: 14,
    color: THEME.utility.textMuted,
    textAlign: 'center',
    lineHeight: 20,
    marginBottom: 4,
  },
  passToolbar: { paddingHorizontal: 22, paddingTop: 14, gap: 10 },
  passModeRow: { flexDirection: 'row', gap: 8, alignItems: 'center' },
  passModePill: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 18,
    backgroundColor: THEME.utility.surfaceMuted,
    borderWidth: 1,
    borderColor: THEME.utility.border,
  },
  passModePillActive: { backgroundColor: THEME.brand.sand, borderColor: THEME.brand.sand },
  passModeText: { fontSize: 12, fontWeight: '700', color: THEME.utility.textMuted },
  passModeTextActive: { color: THEME.utility.text },
  listBtn: {
    marginLeft: 'auto',
    backgroundColor: THEME.brand.ink,
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 18,
  },
  listBtnText: { color: '#fff', fontSize: 12, fontWeight: '700' },
  searchInput: {
    borderWidth: 1,
    borderColor: THEME.utility.border,
    borderRadius: 14,
    paddingVertical: 12,
    paddingHorizontal: 14,
    fontSize: 15,
    backgroundColor: THEME.utility.surface,
    color: THEME.utility.text,
  },
  gridList: { paddingHorizontal: 18, paddingBottom: 40 },
  gridRow: { gap: 12, marginBottom: 12 },
  gridCell: { flex: 1 },
});
