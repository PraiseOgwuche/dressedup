import React, { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  FlatList,
  Modal,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { THEME, SHADOW, utilityTitle } from '../../constants/theme';
import { socialAPI } from '../../services/api';
import { getApiErrorMessage } from '../../services/errors';
import { SocialUserSummary } from '../../types';
import { Button } from '../ui/Button';

type Props = {
  visible: boolean;
  onClose: () => void;
};

export function DiscoverPeopleModal({ visible, onClose }: Props) {
  const [people, setPeople] = useState<SocialUserSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [busyId, setBusyId] = useState<number | null>(null);

  const loadPeople = useCallback(async () => {
    setLoading(true);
    try {
      const rows = await socialAPI.listPeople();
      setPeople(rows.filter((p) => !p.is_self));
    } catch (error) {
      Alert.alert('Error', getApiErrorMessage(error, 'Could not load people.'));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (visible) loadPeople();
  }, [visible, loadPeople]);

  const toggleFollow = async (user: SocialUserSummary) => {
    setBusyId(user.id);
    try {
      const result = await socialAPI.toggleFollow(user.id);
      setPeople((current) =>
        current.map((p) =>
          p.id === user.id
            ? { ...p, is_following: result.following, follower_count: result.follower_count }
            : p,
        ),
      );
    } catch (error) {
      Alert.alert('Error', getApiErrorMessage(error, 'Could not update follow.'));
    } finally {
      setBusyId(null);
    }
  };

  return (
    <Modal visible={visible} animationType="slide" transparent onRequestClose={onClose}>
      <View style={styles.overlay}>
        <View style={styles.sheet}>
          <View style={styles.handle} />
          <Text style={styles.title}>Discover people</Text>
          <Text style={styles.subtitle}>Follow friends to build your Following feed.</Text>

          {loading ? (
            <ActivityIndicator color={THEME.brand.ink} style={styles.loader} />
          ) : (
            <FlatList
              data={people}
              keyExtractor={(item) => item.id.toString()}
              style={styles.list}
              contentContainerStyle={people.length ? styles.listContent : styles.listEmpty}
              ListEmptyComponent={<Text style={styles.empty}>No other members yet.</Text>}
              renderItem={({ item }) => (
                <View style={styles.row}>
                  <View style={styles.avatar}>
                    <Text style={styles.avatarText}>{item.full_name.charAt(0).toUpperCase()}</Text>
                  </View>
                  <View style={styles.meta}>
                    <Text style={styles.name}>{item.full_name}</Text>
                    <Text style={styles.stats}>
                      {item.post_count} fit{item.post_count === 1 ? '' : 's'} · {item.follower_count} follower
                      {item.follower_count === 1 ? '' : 's'}
                    </Text>
                  </View>
                  <Pressable
                    style={[styles.followBtn, item.is_following && styles.followBtnActive]}
                    onPress={() => toggleFollow(item)}
                    disabled={busyId === item.id}
                  >
                    <Text style={[styles.followText, item.is_following && styles.followTextActive]}>
                      {busyId === item.id ? '…' : item.is_following ? 'Following' : 'Follow'}
                    </Text>
                  </Pressable>
                </View>
              )}
            />
          )}

          <Button title="Done" variant="secondary" onPress={onClose} />
        </View>
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
  sheet: {
    backgroundColor: THEME.utility.background,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    paddingHorizontal: 22,
    paddingTop: 10,
    paddingBottom: 24,
    maxHeight: '82%',
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
  list: { maxHeight: 420, marginBottom: 12 },
  listContent: { gap: 12, paddingBottom: 8 },
  listEmpty: { flexGrow: 1, justifyContent: 'center', paddingVertical: 24 },
  empty: { textAlign: 'center', color: THEME.utility.textMuted, fontSize: 14 },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: THEME.utility.border,
  },
  avatar: {
    width: 42,
    height: 42,
    borderRadius: 21,
    backgroundColor: THEME.brand.sand,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: { fontWeight: '700', color: THEME.utility.text },
  meta: { flex: 1 },
  name: { fontSize: 15, fontWeight: '700', color: THEME.utility.text },
  stats: { marginTop: 2, fontSize: 12, color: THEME.utility.textMuted },
  followBtn: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 18,
    backgroundColor: THEME.brand.ink,
  },
  followBtnActive: {
    backgroundColor: THEME.utility.surfaceMuted,
    borderWidth: 1,
    borderColor: THEME.utility.border,
  },
  followText: { color: '#fff', fontSize: 12, fontWeight: '700' },
  followTextActive: { color: THEME.utility.text },
});
