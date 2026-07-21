import React, { useCallback, useEffect, useState } from 'react';
import {
  Alert,
  FlatList,
  Pressable,
  RefreshControl,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useFocusEffect } from 'expo-router';

import { THEME, FONTS, SHADOW, utilityTitle } from '../../constants/theme';
import { socialAPI } from '../../services/api';
import { getApiErrorMessage } from '../../services/errors';
import { getDeviceTimezone } from '../../services/pushNotifications';
import { FeedScope, SocialPost, StreakStats } from '../../types';
import { FeedPostCard } from '../../components/FeedPostCard';
import { StreakCard } from '../../components/StreakBadge';
import { DiscoverPeopleModal } from '../../components/feed/DiscoverPeopleModal';
import { FeedActivitySheet } from '../../components/feed/FeedActivitySheet';
import { PostCommentsModal } from '../../components/feed/PostCommentsModal';
import { Button } from '../../components/ui/Button';
import { useFeedActivityStore } from '../../store/feedActivityStore';

const SCOPES: { key: FeedScope; label: string }[] = [
  { key: 'all', label: 'All' },
  { key: 'following', label: 'Following' },
  { key: 'mine', label: 'Yours' },
];

export default function FeedScreen() {
  const [posts, setPosts] = useState<SocialPost[]>([]);
  const [streak, setStreak] = useState<StreakStats | null>(null);
  const [scope, setScope] = useState<FeedScope>('all');
  const [loading, setLoading] = useState(false);
  const [likingId, setLikingId] = useState<number | null>(null);
  const [commentsPost, setCommentsPost] = useState<SocialPost | null>(null);
  const [discoverOpen, setDiscoverOpen] = useState(false);
  const [activityOpen, setActivityOpen] = useState(false);

  const activityItems = useFeedActivityStore((state) => state.items);
  const activityLoading = useFeedActivityStore((state) => state.loading);
  const unreadCount = useFeedActivityStore((state) => state.unreadCount);
  const refreshActivity = useFeedActivityStore((state) => state.refresh);
  const markActivitySeen = useFeedActivityStore((state) => state.markSeen);

  const loadFeed = useCallback(async () => {
    setLoading(true);
    try {
      const [postsResponse, streakResponse] = await Promise.all([
        socialAPI.listPosts(scope),
        socialAPI.getStreak(getDeviceTimezone()),
      ]);
      setPosts(postsResponse);
      setStreak(streakResponse);
    } catch (error) {
      Alert.alert('Error', getApiErrorMessage(error, 'Could not load the feed.'));
    } finally {
      setLoading(false);
    }
  }, [scope]);

  useFocusEffect(
    useCallback(() => {
      loadFeed();
      refreshActivity();
    }, [loadFeed, refreshActivity]),
  );

  useEffect(() => {
    loadFeed();
  }, [scope]);

  const toggleLike = async (postId: number) => {
    setLikingId(postId);
    try {
      const result = await socialAPI.toggleLike(postId);
      setPosts((current) =>
        current.map((post) =>
          post.id === postId
            ? { ...post, liked_by_me: result.liked, reactions_count: result.reactions_count }
            : post,
        ),
      );
    } catch (error) {
      Alert.alert('Error', getApiErrorMessage(error, 'Could not update like.'));
    } finally {
      setLikingId(null);
    }
  };

  const handleDelete = (post: SocialPost) => {
    Alert.alert('Delete fit', 'Remove this post from the feed?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete',
        style: 'destructive',
        onPress: async () => {
          try {
            await socialAPI.deletePost(post.id);
            setPosts((current) => current.filter((p) => p.id !== post.id));
          } catch (error) {
            Alert.alert('Error', getApiErrorMessage(error, 'Could not delete post.'));
          }
        },
      },
    ]);
  };

  const handleCommentsChange = (postId: number, count: number) => {
    setPosts((current) =>
      current.map((post) => (post.id === postId ? { ...post, comments_count: count } : post)),
    );
    setCommentsPost((current) =>
      current && current.id === postId ? { ...current, comments_count: count } : current,
    );
  };

  const openActivity = async () => {
    setActivityOpen(true);
    await refreshActivity();
    await markActivitySeen();
  };

  const closeActivity = () => setActivityOpen(false);

  const openPostFromActivity = async (postId: number) => {
    setActivityOpen(false);
    const fromFeed = posts.find((post) => post.id === postId);
    if (fromFeed) {
      setCommentsPost(fromFeed);
      return;
    }
    try {
      const post = await socialAPI.getPost(postId);
      setCommentsPost(post);
    } catch (error) {
      Alert.alert('Error', getApiErrorMessage(error, 'Could not open that post.'));
    }
  };

  const emptyCopy =
    scope === 'following'
      ? {
          title: 'Follow people to fill this feed',
          body: 'Discover members and follow their fits. Your own posts show here too.',
          action: 'Discover people',
        }
      : scope === 'mine'
        ? {
            title: 'No fits shared yet',
            body: 'Log what you wore on Home, then tap Share to feed.',
            action: undefined,
          }
        : {
            title: 'The feed is quiet',
            body: 'Be the first to share a fit after logging what you wore on Home.',
            action: undefined,
          };

  const listHeader = (
    <View style={styles.listHeader}>
      <StreakCard streak={streak} />

      <View style={styles.scopeRow}>
        {SCOPES.map(({ key, label }) => {
          const active = scope === key;
          return (
            <Pressable
              key={key}
              style={[styles.scopePill, active && styles.scopePillActive]}
              onPress={() => setScope(key)}
            >
              <Text style={[styles.scopeText, active && styles.scopeTextActive]}>{label}</Text>
            </Pressable>
          );
        })}
        <Pressable style={styles.discoverBtn} onPress={() => setDiscoverOpen(true)}>
          <Text style={styles.discoverText}>People</Text>
        </Pressable>
      </View>
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <View style={styles.headerRow}>
          <View style={styles.headerCopy}>
            <Text style={styles.title}>Feed</Text>
            <Text style={styles.subtitle}>Real fits from logged outfits — mirror photos welcome.</Text>
          </View>
          <Pressable style={styles.activityBtn} onPress={openActivity}>
            <Text style={styles.activityIcon}>🔔</Text>
            {unreadCount > 0 ? (
              <View style={styles.activityBadge}>
                <Text style={styles.activityBadgeText}>
                  {unreadCount > 9 ? '9+' : unreadCount}
                </Text>
              </View>
            ) : null}
          </Pressable>
        </View>
      </View>

      <FlatList
        data={posts}
        keyExtractor={(item) => item.id.toString()}
        onRefresh={loadFeed}
        refreshing={loading}
        contentContainerStyle={posts.length ? styles.list : styles.emptyList}
        ListHeaderComponent={listHeader}
        ItemSeparatorComponent={() => <View style={styles.separator} />}
        ListEmptyComponent={
          !loading ? (
            <View style={styles.emptyState}>
              <Text style={styles.emptyEmoji}>✨</Text>
              <Text style={styles.emptyTitle}>{emptyCopy.title}</Text>
              <Text style={styles.emptyBody}>{emptyCopy.body}</Text>
              {emptyCopy.action ? (
                <Button title={emptyCopy.action} onPress={() => setDiscoverOpen(true)} />
              ) : null}
            </View>
          ) : null
        }
        renderItem={({ item }) => (
          <FeedPostCard
            post={item}
            likeLoading={likingId === item.id}
            onToggleLike={() => toggleLike(item.id)}
            onOpenComments={() => setCommentsPost(item)}
            onDelete={item.is_mine ? () => handleDelete(item) : undefined}
          />
        )}
      />

      <PostCommentsModal
        visible={!!commentsPost}
        post={commentsPost}
        onClose={() => setCommentsPost(null)}
        onCommentsChange={handleCommentsChange}
      />
      <DiscoverPeopleModal visible={discoverOpen} onClose={() => setDiscoverOpen(false)} />
      <FeedActivitySheet
        visible={activityOpen}
        items={activityItems}
        loading={activityLoading}
        onClose={closeActivity}
        onOpenPost={openPostFromActivity}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: THEME.utility.background,
  },
  header: {
    paddingHorizontal: 22,
    paddingTop: 12,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: THEME.utility.border,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
  },
  headerCopy: {
    flex: 1,
  },
  activityBtn: {
    width: 42,
    height: 42,
    borderRadius: 21,
    backgroundColor: THEME.utility.surfaceMuted,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: THEME.utility.border,
  },
  activityIcon: {
    fontSize: 18,
  },
  activityBadge: {
    position: 'absolute',
    top: -4,
    right: -4,
    minWidth: 18,
    height: 18,
    borderRadius: 9,
    paddingHorizontal: 4,
    backgroundColor: THEME.editorial.accentDark,
    alignItems: 'center',
    justifyContent: 'center',
  },
  activityBadgeText: {
    color: '#fff',
    fontSize: 10,
    fontWeight: '700',
  },
  title: {
    ...utilityTitle(28),
    textAlign: 'left',
  },
  subtitle: {
    fontSize: 14,
    color: THEME.utility.textMuted,
    marginTop: 4,
    lineHeight: 20,
  },
  listHeader: {
    gap: 14,
    marginBottom: 8,
  },
  scopeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  scopePill: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: THEME.utility.surface,
    borderWidth: 1,
    borderColor: THEME.utility.border,
  },
  scopePillActive: {
    backgroundColor: THEME.brand.accent,
    borderColor: THEME.brand.accent,
  },
  scopeText: {
    fontSize: 13,
    fontWeight: '600',
    color: THEME.utility.text,
  },
  scopeTextActive: {
    color: '#fff',
  },
  discoverBtn: {
    marginLeft: 'auto',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 18,
    backgroundColor: THEME.brand.mist,
  },
  discoverText: {
    fontSize: 12,
    fontWeight: '700',
    color: THEME.utility.text,
  },
  list: {
    paddingHorizontal: 22,
    paddingTop: 16,
    paddingBottom: 40,
  },
  separator: { height: 16 },
  emptyList: {
    flexGrow: 1,
    paddingHorizontal: 22,
    paddingBottom: 40,
  },
  emptyState: {
    alignItems: 'center',
    backgroundColor: THEME.utility.surfaceMuted,
    borderRadius: 20,
    padding: 28,
    marginTop: 8,
    gap: 10,
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
});
