import React from 'react';
import {
  ActivityIndicator,
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useRouter } from 'expo-router';

import { THEME, FONTS, SHADOW } from '../../constants/theme';
import { FeedActivityItem } from '../../types';

const TYPE_EMOJI: Record<FeedActivityItem['type'], string> = {
  like: '♥',
  comment: '💬',
  follow: '＋',
  new_post: '◎',
  streak_nudge: '🔥',
  listing_interest: '♻️',
};

function formatWhen(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return '';
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

type FeedActivitySheetProps = {
  visible: boolean;
  items: FeedActivityItem[];
  loading: boolean;
  onClose: () => void;
  onOpenPost?: (postId: number) => void;
};

export function FeedActivitySheet({
  visible,
  items,
  loading,
  onClose,
  onOpenPost,
}: FeedActivitySheetProps) {
  const router = useRouter();

  const handlePress = (item: FeedActivityItem) => {
    if (item.type === 'streak_nudge') {
      onClose();
      router.push('/(tabs)/home');
      return;
    }
    if (item.post_id && onOpenPost) {
      onOpenPost(item.post_id);
    }
  };

  return (
    <Modal visible={visible} animationType="slide" transparent onRequestClose={onClose}>
      <Pressable style={styles.backdrop} onPress={onClose}>
        <Pressable style={styles.sheet} onPress={(e) => e.stopPropagation()}>
          <View style={styles.handle} />
          <Text style={styles.title}>Activity</Text>
          <Text style={styles.subtitle}>Likes, comments, follows, and streak reminders.</Text>

          {loading && items.length === 0 ? (
            <View style={styles.loadingBox}>
              <ActivityIndicator color={THEME.editorial.accentDark} />
            </View>
          ) : items.length === 0 ? (
            <View style={styles.emptyBox}>
              <Text style={styles.emptyEmoji}>✨</Text>
              <Text style={styles.emptyTitle}>All caught up</Text>
              <Text style={styles.emptyBody}>
                When someone engages with your fits or people you follow post, it shows up here.
              </Text>
            </View>
          ) : (
            <ScrollView style={styles.list} contentContainerStyle={styles.listContent}>
              {items.map((item) => {
                const tappable = item.type === 'streak_nudge' || !!item.post_id;
                return (
                  <Pressable
                    key={item.id}
                    style={[styles.row, item.is_unread && styles.rowUnread]}
                    onPress={tappable ? () => handlePress(item) : undefined}
                    disabled={!tappable}
                  >
                    <View style={styles.iconWrap}>
                      <Text style={styles.icon}>{TYPE_EMOJI[item.type]}</Text>
                    </View>
                    <View style={styles.copy}>
                      <Text style={styles.message}>
                        <Text style={styles.actor}>{item.actor_name}</Text> {item.message}
                      </Text>
                      <Text style={styles.when}>{formatWhen(item.created_at)}</Text>
                    </View>
                    {item.is_unread ? <View style={styles.dot} /> : null}
                  </Pressable>
                );
              })}
            </ScrollView>
          )}

          <Pressable style={styles.closeBtn} onPress={onClose}>
            <Text style={styles.closeText}>Done</Text>
          </Pressable>
        </Pressable>
      </Pressable>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: 'rgba(28, 28, 28, 0.45)',
    justifyContent: 'flex-end',
  },
  sheet: {
    maxHeight: '78%',
    backgroundColor: THEME.utility.surface,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    paddingHorizontal: 22,
    paddingBottom: 28,
    ...SHADOW.soft,
  },
  handle: {
    alignSelf: 'center',
    width: 40,
    height: 4,
    borderRadius: 2,
    backgroundColor: THEME.utility.border,
    marginTop: 10,
    marginBottom: 16,
  },
  title: {
    fontFamily: FONTS.sans,
    fontSize: 22,
    fontWeight: '700',
    color: THEME.utility.text,
  },
  subtitle: {
    fontSize: 13,
    color: THEME.utility.textMuted,
    marginTop: 4,
    marginBottom: 16,
    lineHeight: 18,
  },
  loadingBox: {
    paddingVertical: 40,
    alignItems: 'center',
  },
  emptyBox: {
    alignItems: 'center',
    paddingVertical: 28,
    paddingHorizontal: 12,
    gap: 8,
  },
  emptyEmoji: { fontSize: 40 },
  emptyTitle: {
    fontSize: 17,
    fontWeight: '700',
    color: THEME.utility.text,
  },
  emptyBody: {
    fontSize: 14,
    color: THEME.utility.textMuted,
    textAlign: 'center',
    lineHeight: 20,
  },
  list: {
    maxHeight: 360,
  },
  listContent: {
    gap: 8,
    paddingBottom: 8,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
    padding: 12,
    borderRadius: 14,
    backgroundColor: THEME.utility.surfaceMuted,
    borderWidth: 1,
    borderColor: THEME.utility.border,
  },
  rowUnread: {
    borderColor: THEME.brand.mist,
    backgroundColor: THEME.utility.surfaceMuted,
  },
  iconWrap: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: THEME.utility.surface,
    alignItems: 'center',
    justifyContent: 'center',
  },
  icon: {
    fontSize: 16,
  },
  copy: {
    flex: 1,
    gap: 4,
  },
  message: {
    fontSize: 14,
    color: THEME.utility.text,
    lineHeight: 20,
  },
  actor: {
    fontWeight: '700',
  },
  when: {
    fontSize: 12,
    color: THEME.utility.textMuted,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: THEME.editorial.accentDark,
    marginTop: 6,
  },
  closeBtn: {
    marginTop: 14,
    alignItems: 'center',
    paddingVertical: 14,
    borderRadius: 14,
    backgroundColor: THEME.brand.accent,
  },
  closeText: {
    color: '#fff',
    fontSize: 15,
    fontWeight: '700',
  },
});
