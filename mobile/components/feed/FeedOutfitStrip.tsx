import React from 'react';
import { Image, ScrollView, StyleSheet, Text, View } from 'react-native';

import { mediaUrl } from '../../constants/config';
import { THEME } from '../../constants/theme';
import { ClosetItem } from '../../types';

type Props = {
  top?: ClosetItem | null;
  bottom?: ClosetItem | null;
  shoes?: ClosetItem | null;
  outerwear?: ClosetItem | null;
};

const pieces = (props: Props) =>
  [
    { label: 'Top', item: props.top },
    { label: 'Bottom', item: props.bottom },
    { label: 'Shoes', item: props.shoes },
    { label: 'Layer', item: props.outerwear },
  ].filter((p) => p.item);

export function FeedOutfitStrip(props: Props) {
  const items = pieces(props);
  if (!items.length) return null;

  return (
    <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.row}>
      {items.map(({ label, item }) => {
        const uri = mediaUrl(item?.thumbnail_url ?? item?.image_url);
        return (
          <View key={label} style={styles.tile}>
            {uri ? (
              <Image source={{ uri }} style={styles.image} resizeMode="cover" />
            ) : (
              <View style={styles.placeholder}>
                <Text style={styles.emoji}>👕</Text>
              </View>
            )}
            <Text style={styles.label} numberOfLines={1}>
              {item?.name}
            </Text>
          </View>
        );
      })}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  row: { gap: 10, paddingVertical: 2 },
  tile: { width: 72 },
  image: {
    width: 72,
    height: 88,
    borderRadius: 12,
    backgroundColor: THEME.editorial.pill,
  },
  placeholder: {
    width: 72,
    height: 88,
    borderRadius: 12,
    backgroundColor: THEME.editorial.pill,
    alignItems: 'center',
    justifyContent: 'center',
  },
  emoji: { fontSize: 24 },
  label: {
    marginTop: 6,
    fontSize: 10,
    fontWeight: '600',
    color: THEME.utility.textMuted,
  },
});
