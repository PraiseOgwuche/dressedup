import React from 'react';
import { View, Text, StyleSheet, Image, Pressable } from 'react-native';

import { THEME, SHADOW } from '../constants/theme';
import { mediaUrl } from '../constants/config';
import { OutfitCard } from './OutfitCard';
import { SocialPost } from '../types';

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
  likeLoading?: boolean;
}

export function FeedPostCard({ post, onToggleLike, likeLoading }: FeedPostCardProps) {
  const firstName = post.user_name?.trim().split(/\s+/)[0] || 'User';

  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>{firstName.charAt(0).toUpperCase()}</Text>
        </View>
        <View style={styles.headerText}>
          <Text style={styles.name}>{post.user_name}</Text>
          <Text style={styles.when}>{formatWhen(post.created_at)}</Text>
        </View>
      </View>

      {!!post.caption && <Text style={styles.caption}>{post.caption}</Text>}

      {!!post.photo_url && (
        <Image source={{ uri: mediaUrl(post.photo_url) }} style={styles.photo} resizeMode="cover" />
      )}

      <OutfitCard
        variant="utility"
        title="Outfit"
        top={post.top}
        bottom={post.bottom}
        shoes={post.shoes}
        outerwear={post.outerwear}
      />

      <Pressable
        style={[styles.likeRow, post.liked_by_me && styles.likeRowActive]}
        onPress={onToggleLike}
        disabled={likeLoading}
      >
        <Text style={[styles.likeIcon, post.liked_by_me && styles.likeIconActive]}>
          {post.liked_by_me ? '♥' : '♡'}
        </Text>
        <Text style={[styles.likeCount, post.liked_by_me && styles.likeCountActive]}>
          {post.reactions_count} {post.reactions_count === 1 ? 'like' : 'likes'}
        </Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: THEME.utility.surface,
    borderRadius: 18,
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
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: THEME.brand.sand,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: {
    fontSize: 16,
    fontWeight: '700',
    color: THEME.utility.text,
  },
  headerText: {
    flex: 1,
  },
  name: {
    fontSize: 15,
    fontWeight: '700',
    color: THEME.utility.text,
  },
  when: {
    fontSize: 12,
    color: THEME.utility.textMuted,
    marginTop: 2,
  },
  caption: {
    fontSize: 15,
    lineHeight: 21,
    color: THEME.utility.text,
  },
  photo: {
    width: '100%',
    height: 260,
    borderRadius: 14,
    backgroundColor: THEME.utility.surfaceMuted,
  },
  likeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    alignSelf: 'flex-start',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 999,
    backgroundColor: THEME.utility.surfaceMuted,
  },
  likeRowActive: {
    backgroundColor: THEME.brand.sand,
  },
  likeIcon: {
    fontSize: 18,
    color: THEME.utility.textMuted,
  },
  likeIconActive: {
    color: THEME.shared.error,
  },
  likeCount: {
    fontSize: 13,
    fontWeight: '600',
    color: THEME.utility.textMuted,
  },
  likeCountActive: {
    color: THEME.utility.text,
  },
});
