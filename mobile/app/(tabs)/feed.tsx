import React, { useCallback, useState } from 'react';
import { Alert, FlatList, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useFocusEffect } from 'expo-router';

import { THEME, utilityTitle } from '../../constants/theme';
import { socialAPI } from '../../services/api';
import { getApiErrorMessage } from '../../services/errors';
import { SocialPost } from '../../types';
import { FeedPostCard } from '../../components/FeedPostCard';

export default function FeedScreen() {
  const [posts, setPosts] = useState<SocialPost[]>([]);
  const [loading, setLoading] = useState(false);
  const [likingId, setLikingId] = useState<number | null>(null);

  const loadPosts = useCallback(async () => {
    setLoading(true);
    try {
      const response = await socialAPI.listPosts();
      setPosts(response);
    } catch (error) {
      Alert.alert('Error', getApiErrorMessage(error, 'Could not load the feed.'));
    } finally {
      setLoading(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      loadPosts();
    }, [loadPosts]),
  );

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

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Feed</Text>
        <Text style={styles.subtitle}>Fits shared after you log what you wore.</Text>
      </View>
      <FlatList
        data={posts}
        keyExtractor={(item) => item.id.toString()}
        onRefresh={loadPosts}
        refreshing={loading}
        contentContainerStyle={posts.length ? styles.list : styles.emptyList}
        ListEmptyComponent={
          <Text style={styles.empty}>No fits yet. Log an outfit on Home and share it here.</Text>
        }
        renderItem={({ item }) => (
          <FeedPostCard
            post={item}
            likeLoading={likingId === item.id}
            onToggleLike={() => toggleLike(item.id)}
          />
        )}
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
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: THEME.utility.border,
    gap: 4,
  },
  title: {
    ...utilityTitle(28),
    textAlign: 'left',
  },
  subtitle: {
    fontSize: 14,
    color: THEME.utility.textMuted,
  },
  list: {
    paddingHorizontal: 22,
    paddingTop: 16,
    paddingBottom: 40,
    gap: 16,
  },
  emptyList: {
    flexGrow: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 32,
  },
  empty: {
    fontSize: 16,
    color: THEME.utility.textMuted,
    textAlign: 'center',
    lineHeight: 22,
  },
});
