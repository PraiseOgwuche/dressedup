import React from 'react';
import { Alert, Image, Pressable, StyleSheet, Text, View } from 'react-native';

import { mediaUrl } from '../../constants/config';
import { THEME, FONTS, SHADOW } from '../../constants/theme';
import { marketplaceAPI } from '../../services/api';
import { getApiErrorMessage } from '../../services/errors';
import { openExternalUrl } from '../../services/openUrl';
import { MyListingInterest } from '../../types';

type Props = {
  interest: MyListingInterest;
  onChanged?: () => void;
};

function formatPrice(cents?: number | null) {
  if (cents == null) return 'Free';
  return `$${(cents / 100).toFixed(cents % 100 === 0 ? 0 : 2)}`;
}

export function MyInterestCard({ interest, onChanged }: Props) {
  const listing = interest.listing;
  const thumb = mediaUrl(listing.item.thumbnail_url ?? listing.item.image_url);
  const gone = listing.status !== 'active';

  const contactAgain = async () => {
    try {
      const result = await marketplaceAPI.interest(listing.id);
      await openExternalUrl(result.mailto);
      onChanged?.();
    } catch (error) {
      Alert.alert('Error', getApiErrorMessage(error, 'Could not contact seller.'));
    }
  };

  return (
    <View style={[styles.card, gone && styles.cardGone]}>
      <View style={styles.imageWrap}>
        {thumb ? (
          <Image source={{ uri: thumb }} style={styles.image} resizeMode="cover" />
        ) : (
          <View style={styles.placeholder}>
            <Text style={styles.placeholderEmoji}>👕</Text>
          </View>
        )}
        {gone ? (
          <View style={styles.goneBadge}>
            <Text style={styles.goneText}>No longer available</Text>
          </View>
        ) : null}
      </View>
      <View style={styles.body}>
        <Text style={styles.title}>{listing.title}</Text>
        <Text style={styles.meta}>
          {listing.seller_name} · {formatPrice(listing.price_cents)}
        </Text>
        <Text style={styles.when}>
          You expressed interest {new Date(interest.expressed_at).toLocaleDateString()}
        </Text>
        {!gone ? (
          <Pressable style={styles.contactBtn} onPress={contactAgain}>
            <Text style={styles.contactBtnText}>Email seller again</Text>
          </Pressable>
        ) : null}
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
  cardGone: { opacity: 0.72 },
  imageWrap: {
    width: '100%',
    aspectRatio: 3 / 4,
    backgroundColor: THEME.editorial.pill,
    position: 'relative',
  },
  image: { width: '100%', height: '100%' },
  placeholder: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  placeholderEmoji: { fontSize: 40 },
  goneBadge: {
    position: 'absolute',
    inset: 0,
    backgroundColor: 'rgba(28,28,28,0.45)',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 12,
  },
  goneText: { color: '#fff', fontWeight: '700', fontSize: 13, textAlign: 'center' },
  body: { padding: 14, gap: 6 },
  title: {
    fontFamily: FONTS.sans,
    fontSize: 16,
    fontWeight: '700',
    color: THEME.utility.text,
  },
  meta: { fontSize: 12, color: THEME.utility.textMuted },
  when: { fontSize: 12, color: THEME.utility.textMuted },
  contactBtn: {
    marginTop: 8,
    backgroundColor: THEME.brand.ink,
    borderRadius: 12,
    paddingVertical: 10,
    alignItems: 'center',
  },
  contactBtnText: { color: '#fff', fontSize: 13, fontWeight: '700' },
});
