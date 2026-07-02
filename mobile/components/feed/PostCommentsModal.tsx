import React, { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  FlatList,
  KeyboardAvoidingView,
  Modal,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';

import { THEME, SHADOW, utilityTitle } from '../../constants/theme';
import { socialAPI } from '../../services/api';
import { getApiErrorMessage } from '../../services/errors';
import { SocialComment, SocialPost } from '../../types';
import { Button } from '../ui/Button';

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

type Props = {
  visible: boolean;
  post: SocialPost | null;
  onClose: () => void;
  onCommentsChange: (postId: number, count: number) => void;
};

export function PostCommentsModal({ visible, post, onClose, onCommentsChange }: Props) {
  const [comments, setComments] = useState<SocialComment[]>([]);
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [draft, setDraft] = useState('');

  const loadComments = useCallback(async () => {
    if (!post) return;
    setLoading(true);
    try {
      const rows = await socialAPI.listComments(post.id);
      setComments(rows);
      onCommentsChange(post.id, rows.length);
    } catch (error) {
      Alert.alert('Error', getApiErrorMessage(error, 'Could not load comments.'));
    } finally {
      setLoading(false);
    }
  }, [post, onCommentsChange]);

  useEffect(() => {
    if (visible && post) {
      setDraft('');
      loadComments();
    }
  }, [visible, post, loadComments]);

  const handleSend = async () => {
    const body = draft.trim();
    if (!post || body.length < 1) return;
    setSending(true);
    try {
      const created = await socialAPI.addComment(post.id, body);
      setComments((current) => {
        const next = [...current, created];
        onCommentsChange(post.id, next.length);
        return next;
      });
      setDraft('');
    } catch (error) {
      Alert.alert('Error', getApiErrorMessage(error, 'Could not post comment.'));
    } finally {
      setSending(false);
    }
  };

  const handleDelete = (comment: SocialComment) => {
    Alert.alert('Delete comment', 'Remove this comment?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete',
        style: 'destructive',
        onPress: async () => {
          if (!post) return;
          try {
            await socialAPI.deleteComment(comment.id);
            setComments((current) => {
              const next = current.filter((c) => c.id !== comment.id);
              onCommentsChange(post.id, next.length);
              return next;
            });
          } catch (error) {
            Alert.alert('Error', getApiErrorMessage(error, 'Could not delete comment.'));
          }
        },
      },
    ]);
  };

  if (!post) return null;

  return (
    <Modal visible={visible} animationType="slide" transparent onRequestClose={onClose}>
      <View style={styles.overlay}>
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : undefined}
          style={styles.sheetWrap}
        >
          <View style={styles.sheet}>
            <View style={styles.handle} />
            <Text style={styles.title}>Comments</Text>
            <Text style={styles.subtitle}>{post.user_name}&apos;s fit</Text>

            {loading ? (
              <ActivityIndicator color={THEME.brand.ink} style={styles.loader} />
            ) : (
              <FlatList
                data={comments}
                keyExtractor={(item) => item.id.toString()}
                style={styles.list}
                contentContainerStyle={comments.length ? styles.listContent : styles.listEmpty}
                ListEmptyComponent={
                  <Text style={styles.empty}>Be the first to comment on this fit.</Text>
                }
                renderItem={({ item }) => (
                  <Pressable
                    style={styles.commentRow}
                    onLongPress={item.is_mine ? () => handleDelete(item) : undefined}
                  >
                    <View style={styles.commentAvatar}>
                      <Text style={styles.commentAvatarText}>
                        {item.user_name.charAt(0).toUpperCase()}
                      </Text>
                    </View>
                    <View style={styles.commentBody}>
                      <View style={styles.commentHeader}>
                        <Text style={styles.commentName}>{item.user_name}</Text>
                        <Text style={styles.commentWhen}>{formatWhen(item.created_at)}</Text>
                      </View>
                      <Text style={styles.commentText}>{item.body}</Text>
                    </View>
                  </Pressable>
                )}
              />
            )}

            <View style={styles.composer}>
              <TextInput
                style={styles.input}
                placeholder="Add a comment…"
                placeholderTextColor={THEME.utility.textMuted}
                value={draft}
                onChangeText={setDraft}
                multiline
              />
              <Button title="Post" loading={sending} onPress={handleSend} style={styles.postBtn} />
            </View>
            <Button title="Close" variant="secondary" onPress={onClose} />
          </View>
        </KeyboardAvoidingView>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(28, 28, 28, 0.45)',
    justifyContent: 'flex-end',
  },
  sheetWrap: { maxHeight: '88%' },
  sheet: {
    backgroundColor: THEME.utility.background,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    paddingHorizontal: 22,
    paddingTop: 10,
    paddingBottom: 24,
    ...SHADOW.soft,
  },
  handle: {
    alignSelf: 'center',
    width: 44,
    height: 4,
    borderRadius: 2,
    backgroundColor: THEME.utility.border,
    marginBottom: 14,
  },
  title: { ...utilityTitle(22), textAlign: 'left' },
  subtitle: { fontSize: 13, color: THEME.utility.textMuted, marginBottom: 12 },
  loader: { marginVertical: 24 },
  list: { maxHeight: 340 },
  listContent: { gap: 14, paddingBottom: 8 },
  listEmpty: { flexGrow: 1, justifyContent: 'center', paddingVertical: 24 },
  empty: { textAlign: 'center', color: THEME.utility.textMuted, fontSize: 14 },
  commentRow: { flexDirection: 'row', gap: 10 },
  commentAvatar: {
    width: 34,
    height: 34,
    borderRadius: 17,
    backgroundColor: THEME.brand.sand,
    alignItems: 'center',
    justifyContent: 'center',
  },
  commentAvatarText: { fontWeight: '700', color: THEME.utility.text },
  commentBody: { flex: 1 },
  commentHeader: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  commentName: { fontSize: 13, fontWeight: '700', color: THEME.utility.text },
  commentWhen: { fontSize: 11, color: THEME.utility.textMuted },
  commentText: { marginTop: 4, fontSize: 14, lineHeight: 20, color: THEME.utility.text },
  composer: { flexDirection: 'row', gap: 10, alignItems: 'flex-end', marginTop: 12, marginBottom: 10 },
  input: {
    flex: 1,
    minHeight: 44,
    maxHeight: 100,
    borderWidth: 1,
    borderColor: THEME.utility.border,
    borderRadius: 14,
    paddingHorizontal: 14,
    paddingVertical: 10,
    fontSize: 15,
    color: THEME.utility.text,
    backgroundColor: THEME.utility.surface,
  },
  postBtn: { minWidth: 84 },
});
