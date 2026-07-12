import React from 'react';
import { ActivityIndicator, Image, Pressable, StyleSheet, Text, View } from 'react-native';

import { mediaUrl } from '../../constants/config';
import { THEME, FONTS, SHADOW } from '../../constants/theme';
import { ClosetItem } from '../../types';

type Props = {
  item: ClosetItem;
  onPress: () => void;
  onWear?: () => void;
  onSoilOrWash?: () => void;
  onMarkReviewed?: () => void;
  busy?: boolean;
};

function isCutoutUrl(url?: string | null): boolean {
  return Boolean(url && url.includes('/cutouts/'));
}

export function ClosetGridCard({
  item,
  onPress,
  onWear,
  onSoilOrWash,
  onMarkReviewed,
  busy = false,
}: Props) {
  const thumbPath = item.thumbnail_url ?? item.image_url;
  const thumb = mediaUrl(thumbPath);
  const cutout = isCutoutUrl(item.thumbnail_url);

  return (
    <Pressable style={styles.card} onPress={onPress}>
      <View style={[styles.imageWrap, cutout && styles.imageWrapCutout]}>
        {thumb ? (
          <Image
            source={{ uri: thumb }}
            style={styles.image}
            resizeMode={cutout ? 'contain' : 'cover'}
          />
        ) : (
          <View style={styles.placeholder}>
            <Text style={styles.placeholderEmoji}>👕</Text>
          </View>
        )}
        {!item.is_clean ? <View style={styles.dirtyVeil} /> : null}
        <View style={styles.badges}>
          {item.needs_review ? (
            <View style={[styles.badge, styles.reviewBadge]}>
              <Text style={styles.badgeText}>Review</Text>
            </View>
          ) : null}
          {!item.is_clean ? (
            <View style={[styles.badge, styles.dirtyBadge]}>
              <Text style={styles.badgeText}>Hamper</Text>
            </View>
          ) : null}
        </View>
        {item.color_hex ? (
          <View style={[styles.colorDot, { backgroundColor: item.color_hex }]} />
        ) : null}
        {busy ? (
          <View style={styles.busyOverlay}>
            <ActivityIndicator color="#fff" />
          </View>
        ) : null}
      </View>
      <View style={styles.footer}>
        <Text style={styles.name} numberOfLines={2}>
          {item.name}
        </Text>
        <Text style={styles.meta} numberOfLines={1}>
          {[item.brand, item.subcategory ?? item.category].filter(Boolean).join(' · ')}
        </Text>
        <View style={styles.actions}>
          {onWear ? (
            <Pressable
              style={styles.actionBtn}
              onPress={(e) => {
                e.stopPropagation?.();
                onWear();
              }}
              disabled={busy}
            >
              <Text style={styles.actionText}>Wore</Text>
            </Pressable>
          ) : null}
          {onSoilOrWash ? (
            <Pressable
              style={styles.actionBtn}
              onPress={(e) => {
                e.stopPropagation?.();
                onSoilOrWash();
              }}
              disabled={busy}
            >
              <Text style={styles.actionText}>{item.is_clean ? 'Hamper' : 'Wash'}</Text>
            </Pressable>
          ) : null}
          {item.needs_review && onMarkReviewed ? (
            <Pressable
              style={[styles.actionBtn, styles.actionBtnAccent]}
              onPress={(e) => {
                e.stopPropagation?.();
                onMarkReviewed();
              }}
              disabled={busy}
            >
              <Text style={[styles.actionText, styles.actionTextAccent]}>OK</Text>
            </Pressable>
          ) : null}
        </View>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    flex: 1,
    backgroundColor: THEME.utility.surface,
    borderRadius: 18,
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
  imageWrapCutout: {
    backgroundColor: THEME.brand.sand,
    padding: 10,
  },
  image: { width: '100%', height: '100%' },
  placeholder: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  placeholderEmoji: { fontSize: 40 },
  dirtyVeil: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(28, 28, 28, 0.12)',
  },
  busyOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0,0,0,0.35)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  badges: {
    position: 'absolute',
    top: 10,
    left: 10,
    right: 10,
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 10,
  },
  reviewBadge: { backgroundColor: THEME.shared.warning },
  dirtyBadge: { backgroundColor: 'rgba(28, 28, 28, 0.72)' },
  badgeText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#fff',
    letterSpacing: 0.3,
    textTransform: 'uppercase',
  },
  colorDot: {
    position: 'absolute',
    bottom: 10,
    right: 10,
    width: 18,
    height: 18,
    borderRadius: 9,
    borderWidth: 2,
    borderColor: '#fff',
  },
  footer: { paddingHorizontal: 10, paddingTop: 10, paddingBottom: 10 },
  name: {
    fontFamily: FONTS.sans,
    fontSize: 13,
    fontWeight: '700',
    color: THEME.utility.text,
    lineHeight: 17,
  },
  meta: {
    marginTop: 4,
    fontSize: 11,
    color: THEME.utility.textMuted,
    textTransform: 'capitalize',
  },
  actions: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    marginTop: 8,
  },
  actionBtn: {
    paddingHorizontal: 8,
    paddingVertical: 5,
    borderRadius: 10,
    backgroundColor: THEME.utility.surfaceMuted,
    borderWidth: 1,
    borderColor: THEME.utility.border,
  },
  actionBtnAccent: {
    backgroundColor: THEME.brand.ink,
    borderColor: THEME.brand.ink,
  },
  actionText: {
    fontSize: 10,
    fontWeight: '700',
    color: THEME.brand.ink,
    textTransform: 'uppercase',
    letterSpacing: 0.3,
  },
  actionTextAccent: { color: '#fff' },
});
