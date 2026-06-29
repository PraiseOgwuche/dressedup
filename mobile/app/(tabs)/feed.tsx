import React, { useCallback, useState } from 'react';
import { Alert, FlatList, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useFocusEffect } from 'expo-router';

import { COLORS } from '../../constants/config';
import { Input } from '../../components/ui/Input';
import { Button } from '../../components/ui/Button';
import { socialAPI } from '../../services/api';
import { SocialPost } from '../../types';

export default function FeedScreen() {
  const [posts, setPosts] = useState<SocialPost[]>([]);
  const [caption, setCaption] = useState('');
  const [loading, setLoading] = useState(false);

  const loadPosts = useCallback(async () => {
    setLoading(true);
    try {
      const response = await socialAPI.listPosts();
      setPosts(response);
    } catch {
      Alert.alert('Error', 'Could not load social posts.');
    } finally {
      setLoading(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      loadPosts();
    }, [loadPosts]),
  );

  const createPost = async () => {
    if (!caption.trim()) {
      Alert.alert('Add a caption', 'Write a caption before posting.');
      return;
    }
    try {
      await socialAPI.createPost({ caption: caption.trim() });
      setCaption('');
      await loadPosts();
    } catch {
      Alert.alert('Error', 'Could not create your post.');
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Feed</Text>
      </View>
      <View style={styles.composer}>
        <Input label="Post a fit update" placeholder="Today I wore..." value={caption} onChangeText={setCaption} />
        <Button title="Share" onPress={createPost} />
      </View>
      <FlatList
        data={posts}
        keyExtractor={(item) => item.id.toString()}
        onRefresh={loadPosts}
        refreshing={loading}
        contentContainerStyle={posts.length ? styles.list : styles.emptyList}
        ListEmptyComponent={<Text style={styles.comingSoon}>No posts yet. Be the first to share.</Text>}
        renderItem={({ item }) => (
          <View style={styles.postCard}>
            <Text style={styles.caption}>{item.caption}</Text>
            <Text style={styles.meta}>Reactions: {item.reactions_count} • Comments: {item.comments_count}</Text>
          </View>
        )}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  header: {
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  title: {
    fontSize: 24,
    fontWeight: '800',
    color: COLORS.text,
    textAlign: 'center',
  },
  content: {
    flex: 1,
  },
  composer: {
    padding: 20,
    paddingBottom: 8,
  },
  list: {
    paddingHorizontal: 20,
    paddingBottom: 40,
    gap: 12,
  },
  emptyList: {
    flexGrow: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  comingSoon: {
    fontSize: 16,
    color: COLORS.textLight,
  },
  postCard: {
    backgroundColor: COLORS.backgroundLight,
    borderRadius: 14,
    padding: 14,
  },
  caption: {
    fontSize: 15,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: 8,
  },
  meta: {
    fontSize: 12,
    color: COLORS.textLight,
  },
});
