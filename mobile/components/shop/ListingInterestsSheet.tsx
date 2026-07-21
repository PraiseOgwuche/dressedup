import React, { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { THEME, FONTS, SHADOW } from '../../constants/theme';
import { marketplaceAPI } from '../../services/api';
import { getApiErrorMessage } from '../../services/errors';
import { openExternalUrl } from '../../services/openUrl';
import { ReceivedListingInterest } from '../../types';

function formatWhen(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return '';
  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

type ListingInterestsSheetProps = {
  visible: boolean;
  listingId: number | null;
  listingTitle?: string;
  onClose: () => void;
};

export function ListingInterestsSheet({
  visible,
  listingId,
  listingTitle,
  onClose,
}: ListingInterestsSheetProps) {
  const [items, setItems] = useState<ReceivedListingInterest[]>([]);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    if (!listingId) return;
    setLoading(true);
    try {
      const response = await marketplaceAPI.listingInterests(listingId);
      setItems(response);
    } catch (error) {
      Alert.alert('Error', getApiErrorMessage(error, 'Could not load interest list.'));
    } finally {
      setLoading(false);
    }
  }, [listingId]);

  useEffect(() => {
    if (visible && listingId) load();
  }, [visible, listingId, load]);

  const reply = async (item: ReceivedListingInterest) => {
    try {
      await openExternalUrl(item.mailto);
    } catch (error) {
      Alert.alert('Error', getApiErrorMessage(error, 'Could not open email.'));
    }
  };

  return (
    <Modal visible={visible} animationType="slide" transparent onRequestClose={onClose}>
      <Pressable style={styles.backdrop} onPress={onClose}>
        <Pressable style={styles.sheet} onPress={(e) => e.stopPropagation()}>
          <View style={styles.handle} />
          <Text style={styles.title}>Interested buyers</Text>
          <Text style={styles.subtitle}>
            {listingTitle ? `${listingTitle} — ` : ''}reply by email to coordinate off-app.
          </Text>

          {loading ? (
            <View style={styles.loadingBox}>
              <ActivityIndicator color={THEME.editorial.accentDark} />
            </View>
          ) : items.length === 0 ? (
            <View style={styles.emptyBox}>
              <Text style={styles.emptyTitle}>No interest yet</Text>
              <Text style={styles.emptyBody}>When someone taps I&apos;m interested, they show up here.</Text>
            </View>
          ) : (
            <ScrollView style={styles.list} contentContainerStyle={styles.listContent}>
              {items.map((item) => (
                <View key={item.id} style={styles.row}>
                  <View style={styles.copy}>
                    <Text style={styles.name}>{item.buyer_name}</Text>
                    <Text style={styles.when}>Interested {formatWhen(item.created_at)}</Text>
                  </View>
                  <Pressable style={styles.replyBtn} onPress={() => reply(item)}>
                    <Text style={styles.replyText}>Reply</Text>
                  </Pressable>
                </View>
              ))}
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
    maxHeight: '70%',
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
  loadingBox: { paddingVertical: 36, alignItems: 'center' },
  emptyBox: { paddingVertical: 28, gap: 8, alignItems: 'center' },
  emptyTitle: { fontSize: 16, fontWeight: '700', color: THEME.utility.text },
  emptyBody: { fontSize: 13, color: THEME.utility.textMuted, textAlign: 'center', lineHeight: 18 },
  list: { maxHeight: 320 },
  listContent: { gap: 8, paddingBottom: 8 },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    padding: 12,
    borderRadius: 14,
    backgroundColor: THEME.utility.surfaceMuted,
    borderWidth: 1,
    borderColor: THEME.utility.border,
  },
  copy: { flex: 1, gap: 2 },
  name: { fontSize: 15, fontWeight: '700', color: THEME.utility.text },
  when: { fontSize: 12, color: THEME.utility.textMuted },
  replyBtn: {
    backgroundColor: THEME.brand.accent,
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  replyText: { color: '#fff', fontSize: 13, fontWeight: '700' },
  closeBtn: {
    marginTop: 14,
    alignItems: 'center',
    paddingVertical: 14,
    borderRadius: 14,
    backgroundColor: THEME.brand.accent,
  },
  closeText: { color: '#fff', fontSize: 15, fontWeight: '700' },
});
