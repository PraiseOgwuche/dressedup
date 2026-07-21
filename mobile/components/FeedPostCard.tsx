import React from 'react';
import { Alert, Image, Pressable, StyleSheet, Text, View } from 'react-native';

import { THEME, FONTS, SHADOW } from '../constants/theme';
import { mediaUrl } from '../constants/config';
import { SocialPost } from '../types';
import { OutfitLookBoard } from './OutfitLookBoard';
import { FeedOutfitStrip } from './feed/FeedOutfitStrip';

const formatWhen = (iso: string) => {
  const date = new Date(iso);
  const diffMs = Date.now() - date.getTime();
  const mins = Math.floor(diffMs / 60000);
  if (mins < 1) return 'Just now';
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d ago`;
  return date.toLocaleDateString();
};

interface FeedPostCardProps {
  post: SocialPost;
  onToggleLike: () => void;
  onOpenComments: () => void;
  onDelete?: () => void;
  likeLoading?: boolean;
}

export function FeedPostCard({
  post,
  onToggleLike,
  onOpenComments,
  onDelete,
  likeLoading,
}: FeedPostCardProps) {
  const firstName = post.user_name?.trim().split(/\s+/)[0] || 'User';
  const slots = [
    { key: 'top' as const, label: 'Top', item: post.top },
    { key: 'bottom' as const, label: 'Bottom', item: post.bottom },
    { key: 'shoes' as const, label: 'Shoes', item: post.shoes },
    { key: 'outerwear' as const, label: 'Layer', item: post.outerwear },
  ];
  const hasPhoto = !!post.photo_url;

  const handleMenu = () => {
    if (!post.is_mine || !onDelete) return;
    Alert.alert('Your fit', undefined, [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Delete post', style: 'destructive', onPress: onDelete },
    ]);
  };

  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>{firstName.charAt(0).toUpperCase()}</Text>
        </View>
        <View style={styles.headerText}>
          <Text style={styles.name}>{post.user_name}</Text>
          <Text style={styles.when}>
            {formatWhen(post.created_at)}
            {post.following_author && !post.is_mine ? ' · Following' : ''}
          </Text>
        </View>
        {post.is_mine ? (
          <Pressable onPress={handleMenu} hitSlop={8} style={styles.menuBtn}>
            <Text style={styles.menuText}>···</Text>
          </Pressable>
        ) : null}
      </View>

      {post.occasion || post.look_name ? (
        <View style={styles.tagRow}>
          {post.occasion ? (
            <View style={styles.tag}>
              <Text style={styles.tagText}>{post.occasion}</Text>
            </View>
          ) : null}
          {post.look_name ? (
            <View style={[styles.tag, styles.tagMuted]}>
              <Text style={[styles.tagText, styles.tagTextMuted]}>{post.look_name}</Text>
            </View>
          ) : null}
        </View>
      ) : null}

      {!!post.caption && <Text style={styles.caption}>{post.caption}</Text>}

      {hasPhoto ? (
        <>
          <Image
            source={{ uri: mediaUrl(post.photo_url) }}
            style={styles.photo}
            resizeMode="cover"
          />
          <FeedOutfitStrip
            top={post.top}
            bottom={post.bottom}
            shoes={post.shoes}
            outerwear={post.outerwear}
          />
        </>
      ) : (
        <OutfitLookBoard slots={slots} compact />
      )}

      <View style={styles.actions}>
        <Pressable
          style={[styles.actionBtn, post.liked_by_me && styles.actionBtnActive]}
          onPress={onToggleLike}
          disabled={likeLoading}
        >
          <Text style={[styles.actionIcon, post.liked_by_me && styles.actionIconActive]}>
            {post.liked_by_me ? '♥' : '♡'}
          </Text>
          <Text style={[styles.actionLabel, post.liked_by_me && styles.actionLabelActive]}>
            {post.reactions_count}
          </Text>
        </Pressable>

        <Pressable style={styles.actionBtn} onPress={onOpenComments}>
          <Text style={styles.actionIcon}>💬</Text>
          <Text style={styles.actionLabel}>{post.comments_count}</Text>
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: THEME.utility.surface,
    borderRadius: 20,
    padding: 16,
    gap: 12,
    borderWidth: 1,
    borderColor: THEME.utility.border,
    ...SHADOW.soft,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  avatar: {
    width: 42,
    height: 42,
    borderRadius: 21,
    backgroundColor: THEME.brand.mist,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: {
    fontSize: 16,
    fontWeight: '700',
    color: THEME.utility.text,
  },
  headerText: { flex: 1 },
  name: {
    fontFamily: FONTS.sans,
    fontSize: 15,
    fontWeight: '700',
    color: THEME.utility.text,
  },
  when: {
    fontSize: 12,
    color: THEME.utility.textMuted,
    marginTop: 2,
  },
  menuBtn: {
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  menuText: {
    fontSize: 20,
    fontWeight: '700',
    color: THEME.utility.textMuted,
    lineHeight: 20,
  },
  tagRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  tag: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 999,
    backgroundColor: THEME.brand.mist,
  },
  tagMuted: { backgroundColor: THEME.utility.surfaceMuted },
  tagText: {
    fontSize: 11,
    fontWeight: '700',
    color: THEME.utility.text,
    textTransform: 'capitalize',
  },
  tagTextMuted: { color: THEME.utility.textMuted },
  caption: {
    fontSize: 15,
    lineHeight: 21,
    color: THEME.utility.text,
  },
  photo: {
    width: '100%',
    height: 320,
    borderRadius: 16,
    backgroundColor: THEME.editorial.pill,
  },
  actions: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 2,
  },
  actionBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 999,
    backgroundColor: THEME.utility.surfaceMuted,
  },
  actionBtnActive: {
    backgroundColor: THEME.brand.mist,
  },
  actionIcon: {
    fontSize: 16,
    color: THEME.utility.textMuted,
  },
  actionIconActive: {
    color: THEME.shared.error,
  },
  actionLabel: {
    fontSize: 13,
    fontWeight: '700',
    color: THEME.utility.textMuted,
  },
  actionLabelActive: {
    color: THEME.utility.text,
  },
});
