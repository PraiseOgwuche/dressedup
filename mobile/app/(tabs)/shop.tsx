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
import { ShopGapCard } from '../../components/shop/ShopGapCard';
import { ClosetListing, ListingType, MyListingInterest, ShopGapCard as ShopGapCardType, ShopRecommendation } from '../../types';
import { ShopProductCard } from '../../components/shop/ShopProductCard';
import { ShopOutfitPreviewModal } from '../../components/shop/ShopOutfitPreviewModal';
import { MarketplaceListingCard } from '../../components/shop/MarketplaceListingCard';
import { MyInterestCard } from '../../components/shop/MyInterestCard';
import { ListingInterestsSheet } from '../../components/shop/ListingInterestsSheet';
import { CreateListingModal } from '../../components/shop/CreateListingModal';
import { Button } from '../../components/ui/Button';
import { openExternalUrl } from '../../services/openUrl';

type ShopSection = 'picks' | 'passiton';
type PassMode = 'browse' | 'mine' | 'interested';

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
  const [stylingInsight, setStylingInsight] = useState('');
  const [gapCard, setGapCard] = useState<ShopGapCardType | null>(null);
  const [recommendations, setRecommendations] = useState<ShopRecommendation[]>([]);
  const [pickCategory, setPickCategory] = useState('');
  const [pickLoading, setPickLoading] = useState(false);

  const [listings, setListings] = useState<ClosetListing[]>([]);
  const [myListings, setMyListings] = useState<ClosetListing[]>([]);
  const [myInterests, setMyInterests] = useState<MyListingInterest[]>([]);
  const [passFilter, setPassFilter] = useState<ListingType | ''>('');
  const [search, setSearch] = useState('');
  const [passLoading, setPassLoading] = useState(false);
  const [listModalOpen, setListModalOpen] = useState(false);
  const [interestsListing, setInterestsListing] = useState<ClosetListing | null>(null);
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
      setStylingInsight(response.styling_insight ?? '');
      setGapCard(response.gap_card ?? null);
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
      const [browseResult, mineResult, interestedResult] = await Promise.allSettled([
        marketplaceAPI.browse({
          listing_type: passFilter || undefined,
          q: search.trim() || undefined,
        }),
        marketplaceAPI.mine(),
        marketplaceAPI.myInterests(),
      ]);

      if (browseResult.status === 'fulfilled') {
        setListings(browseResult.value);
      }
      if (mineResult.status === 'fulfilled') {
        setMyListings(mineResult.value);
      }
      if (interestedResult.status === 'fulfilled') {
        setMyInterests(interestedResult.value);
      }

      const failed = [browseResult, mineResult, interestedResult].filter(
        (result) => result.status === 'rejected',
      );
      if (failed.length === 3) {
        throw (failed[0] as PromiseRejectedResult).reason;
      }
    } catch (error) {
      Alert.alert('Error', getApiErrorMessage(error, 'Could not load listings.'));
    } finally {
      setPassLoading(false);
    }
  }, [passFilter, search]);

  const handleListingCreated = useCallback(async () => {
    setPassMode('mine');
    setPassFilter('');
    setSearch('');
    await loadPassItOn();
    Alert.alert('Listed', 'Your item is live on Pass it on. Check My listings to manage it.');
  }, [loadPassItOn]);

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

  const previewGapPick = useCallback(() => {
    if (!gapCard?.product_id) return;
    const match = recommendations.find((r) => r.product_id === gapCard.product_id);
    if (match) setPreviewProduct(match);
  }, [gapCard, recommendations]);

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
          <ShopGapCard gap={gapCard} onPreview={gapCard?.product_id ? previewGapPick : undefined} />
          {stylingInsight ? <Text style={styles.insight}>{stylingInsight}</Text> : null}
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
    const data =
      passMode === 'mine'
        ? myListings.filter((l) => l.status === 'active')
        : passMode === 'interested'
          ? []
          : listings;
    const interestData = passMode === 'interested' ? myInterests : [];
    const totalInterestCount = myListings.reduce((sum, l) => sum + (l.interest_count ?? 0), 0);

    return (
      <>
        <View style={styles.passToolbar}>
          <View style={styles.passModeRow}>
            {(['browse', 'mine', 'interested'] as PassMode[]).map((mode) => (
              <Pressable
                key={mode}
                style={[styles.passModePill, passMode === mode && styles.passModePillActive]}
                onPress={() => setPassMode(mode)}
              >
                <Text style={[styles.passModeText, passMode === mode && styles.passModeTextActive]}>
                  {mode === 'browse' ? 'Browse' : mode === 'mine' ? 'My listings' : 'Interested'}
                </Text>
              </Pressable>
            ))}
            <Pressable style={styles.listBtn} onPress={() => setListModalOpen(true)}>
              <Text style={styles.listBtnText}>+ List</Text>
            </Pressable>
          </View>

          {passMode === 'mine' && totalInterestCount > 0 ? (
            <Text style={styles.interestHint}>
              {totalInterestCount} buyer{totalInterestCount === 1 ? '' : 's'} interested across your listings
            </Text>
          ) : null}

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
          data={passMode === 'interested' ? interestData : data}
          keyExtractor={(item) =>
            passMode === 'interested' ? `interest-${item.id}` : item.id.toString()
          }
          numColumns={2}
          columnWrapperStyle={(passMode === 'interested' ? interestData : data).length ? styles.gridRow : undefined}
          onRefresh={loadPassItOn}
          refreshing={passLoading}
          contentContainerStyle={
            (passMode === 'interested' ? interestData : data).length ? styles.gridList : styles.emptyList
          }
          ListEmptyComponent={
            !passLoading ? (
              <View style={styles.emptyState}>
                <Text style={styles.emptyEmoji}>♻️</Text>
                <Text style={styles.emptyTitle}>
                  {passMode === 'mine'
                    ? 'Nothing listed yet'
                    : passMode === 'interested'
                      ? 'No saved interest yet'
                      : 'No listings yet'}
                </Text>
                <Text style={styles.emptyBody}>
                  {passMode === 'mine'
                    ? 'List pieces you want to sell or gift. Buyers show up in your interest list.'
                    : passMode === 'interested'
                      ? 'Tap I\'m interested on a listing — it\'ll show here so you can follow up.'
                      : 'Be the first to pass something on — or check back as the community grows.'}
                </Text>
                {passMode !== 'interested' ? (
                  <Button title="List from closet" onPress={() => setListModalOpen(true)} />
                ) : null}
              </View>
            ) : null
          }
          renderItem={({ item }) => (
            <View style={styles.gridCell}>
              {passMode === 'interested' ? (
                <MyInterestCard interest={item as MyListingInterest} onChanged={loadPassItOn} />
              ) : (
                <MarketplaceListingCard
                  listing={item as ClosetListing}
                  onChanged={loadPassItOn}
                  onViewInterests={setInterestsListing}
                />
              )}
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
        onCreated={handleListingCreated}
      />

      <ShopOutfitPreviewModal
        product={previewProduct}
        visible={previewProduct != null}
        onClose={() => setPreviewProduct(null)}
      />

      <ListingInterestsSheet
        visible={!!interestsListing}
        listingId={interestsListing?.id ?? null}
        listingTitle={interestsListing?.title}
        onClose={() => setInterestsListing(null)}
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
  sectionPillActive: { backgroundColor: THEME.brand.accent, borderColor: THEME.brand.accent },
  sectionText: { fontSize: 13, fontWeight: '700', color: THEME.utility.text },
  sectionTextActive: { color: '#fff' },
  list: { paddingHorizontal: 22, paddingTop: 16, paddingBottom: 40, gap: 14 },
  listHeader: { gap: 12, marginBottom: 8 },
  summary: { fontSize: 15, lineHeight: 22, color: THEME.utility.text, fontWeight: '600' },
  insight: {
    fontSize: 14,
    lineHeight: 20,
    color: THEME.utility.textMuted,
    fontStyle: 'italic',
  },
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
  chipActive: { backgroundColor: THEME.brand.accent, borderColor: THEME.brand.accent },
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
  passModeRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, alignItems: 'center' },
  interestHint: {
    fontSize: 13,
    color: THEME.editorial.accentDark,
    fontWeight: '600',
    lineHeight: 18,
  },
  passModePill: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 18,
    backgroundColor: THEME.utility.surfaceMuted,
    borderWidth: 1,
    borderColor: THEME.utility.border,
  },
  passModePillActive: { backgroundColor: THEME.brand.mist, borderColor: THEME.brand.mist },
  passModeText: { fontSize: 12, fontWeight: '700', color: THEME.utility.textMuted },
  passModeTextActive: { color: THEME.utility.text },
  listBtn: {
    marginLeft: 'auto',
    backgroundColor: THEME.brand.accent,
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
