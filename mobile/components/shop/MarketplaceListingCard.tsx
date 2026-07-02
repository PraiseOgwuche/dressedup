import React from 'react';
import { Alert, Image, Linking, Pressable, StyleSheet, Text, View } from 'react-native';

import { mediaUrl } from '../../constants/config';
import { THEME, FONTS, SHADOW } from '../../constants/theme';
import { marketplaceAPI } from '../../services/api';
import { getApiErrorMessage } from '../../services/errors';
import { ClosetListing } from '../../types';

type Props = {
  listing: ClosetListing;
  onChanged?: () => void;
};

function formatPrice(cents?: number | null) {
  if (cents == null) return 'Free';
  return `$${(cents / 100).toFixed(cents % 100 === 0 ? 0 : 2)}`;
}

export function MarketplaceListingCard({ listing, onChanged }: Props) {
  const thumb = mediaUrl(listing.item.thumbnail_url ?? listing.item.image_url);
  const isGift = listing.listing_type === 'gift';

  const contactSeller = async () => {
    try {
      const result = await marketplaceAPI.interest(listing.id);
      const can = await Linking.canOpenURL(result.mailto);
      if (can) {
        await Linking.openURL(result.mailto);
      } else {
        Alert.alert('Contact seller', `Email ${result.seller_name} from your mail app to coordinate.`);
      }
    } catch (error) {
      Alert.alert('Error', getApiErrorMessage(error, 'Could not start contact.'));
    }
  };

  const markGone = () => {
    Alert.alert('Mark as gone', 'Remove this from the browse feed?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Mark gone',
        onPress: async () => {
          try {
            await marketplaceAPI.markGone(listing.id);
            onChanged?.();
          } catch (error) {
            Alert.alert('Error', getApiErrorMessage(error, 'Could not update listing.'));
          }
        },
      },
    ]);
  };

  const removeListing = () => {
    Alert.alert('Remove listing', 'Take this off Pass it on?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Remove',
        style: 'destructive',
        onPress: async () => {
          try {
            await marketplaceAPI.remove(listing.id);
            onChanged?.();
          } catch (error) {
            Alert.alert('Error', getApiErrorMessage(error, 'Could not remove listing.'));
          }
        },
      },
    ]);
  };

  return (
    <View style={styles.card}>
      <View style={styles.imageWrap}>
        {thumb ? (
          <Image source={{ uri: thumb }} style={styles.image} resizeMode="cover" />
        ) : (
          <View style={styles.placeholder}>
            <Text style={styles.placeholderEmoji}>👕</Text>
          </View>
        )}
        <View style={[styles.typeBadge, isGift && styles.giftBadge]}>
          <Text style={styles.typeBadgeText}>{isGift ? 'Gift' : 'For sale'}</Text>
        </View>
        <View style={styles.priceBadge}>
          <Text style={styles.priceText}>{formatPrice(listing.price_cents)}</Text>
        </View>
      </View>

      <View style={styles.body}>
        <Text style={styles.title}>{listing.title}</Text>
        <Text style={styles.meta}>
          {listing.seller_name} · {listing.condition.replace('_', ' ')} · {listing.item.category}
        </Text>
        {listing.item.brand ? <Text style={styles.brand}>{listing.item.brand}</Text> : null}
        {listing.description ? (
          <Text style={styles.description} numberOfLines={3}>
            {listing.description}
          </Text>
        ) : null}

        {listing.is_mine ? (
          <View style={styles.ownerRow}>
            <Pressable style={styles.secondaryBtn} onPress={markGone}>
              <Text style={styles.secondaryBtnText}>Mark gone</Text>
            </Pressable>
            <Pressable style={styles.secondaryBtn} onPress={removeListing}>
              <Text style={styles.secondaryBtnText}>Remove</Text>
            </Pressable>
          </View>
        ) : (
          <Pressable style={styles.contactBtn} onPress={contactSeller}>
            <Text style={styles.contactBtnText}>Email seller</Text>
          </Pressable>
        )}
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
    aspectRatio: 3 / 4,
    backgroundColor: THEME.editorial.pill,
    position: 'relative',
  },
  image: { width: '100%', height: '100%' },
  placeholder: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  placeholderEmoji: { fontSize: 40 },
  typeBadge: {
    position: 'absolute',
    top: 10,
    left: 10,
    backgroundColor: THEME.brand.ink,
    borderRadius: 10,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  giftBadge: { backgroundColor: THEME.shared.success },
  typeBadgeText: {
    color: '#fff',
    fontSize: 10,
    fontWeight: '700',
    textTransform: 'uppercase',
  },
  priceBadge: {
    position: 'absolute',
    bottom: 10,
    right: 10,
    backgroundColor: 'rgba(28, 28, 28, 0.72)',
    borderRadius: 12,
    paddingHorizontal: 10,
    paddingVertical: 5,
  },
  priceText: { color: '#fff', fontSize: 13, fontWeight: '700' },
  body: { padding: 14, gap: 6 },
  title: {
    fontFamily: FONTS.sans,
    fontSize: 16,
    fontWeight: '700',
    color: THEME.utility.text,
  },
  meta: {
    fontSize: 12,
    color: THEME.utility.textMuted,
    textTransform: 'capitalize',
  },
  brand: { fontSize: 12, fontWeight: '600', color: THEME.editorial.accentDark },
  description: { fontSize: 13, lineHeight: 18, color: THEME.utility.textMuted, marginTop: 4 },
  contactBtn: {
    marginTop: 10,
    backgroundColor: THEME.brand.ink,
    borderRadius: 12,
    paddingVertical: 11,
    alignItems: 'center',
  },
  contactBtnText: { color: '#fff', fontSize: 14, fontWeight: '700' },
  ownerRow: { flexDirection: 'row', gap: 8, marginTop: 10 },
  secondaryBtn: {
    flex: 1,
    borderWidth: 1,
    borderColor: THEME.utility.border,
    borderRadius: 12,
    paddingVertical: 10,
    alignItems: 'center',
    backgroundColor: THEME.utility.surfaceMuted,
  },
  secondaryBtnText: { fontSize: 13, fontWeight: '600', color: THEME.utility.text },
});
