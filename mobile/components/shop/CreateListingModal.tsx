import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Image,
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';

import { mediaUrl } from '../../constants/config';
import { THEME, SHADOW, utilityTitle } from '../../constants/theme';
import { closetAPI, marketplaceAPI } from '../../services/api';
import { getApiErrorMessage } from '../../services/errors';
import { ClosetItem, ListingCondition, ListingType } from '../../types';
import { Button } from '../ui/Button';

type Props = {
  visible: boolean;
  onClose: () => void;
  onCreated: () => void | Promise<void>;
  listedItemIds: number[];
};

const CONDITIONS: ListingCondition[] = ['like_new', 'good', 'fair'];

export function CreateListingModal({ visible, onClose, onCreated, listedItemIds }: Props) {
  const [items, setItems] = useState<ClosetItem[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [listingType, setListingType] = useState<ListingType>('sell');
  const [price, setPrice] = useState('');
  const [condition, setCondition] = useState<ListingCondition>('good');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const available = useMemo(
    () => items.filter((item) => !listedItemIds.includes(item.id)),
    [items, listedItemIds],
  );

  const loadItems = useCallback(async () => {
    setLoading(true);
    try {
      const rows = await closetAPI.list();
      setItems(rows);
    } catch (error) {
      Alert.alert('Error', getApiErrorMessage(error, 'Could not load closet items.'));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (visible) {
      setSelectedId(null);
      setListingType('sell');
      setPrice('');
      setCondition('good');
      setDescription('');
      loadItems();
    }
  }, [visible, loadItems]);

  const handleSubmit = async () => {
    if (!selectedId) {
      Alert.alert('Pick an item', 'Choose something from your closet to list.');
      return;
    }
    let priceCents: number | undefined;
    if (listingType === 'sell') {
      const dollars = parseFloat(price.replace(/[^0-9.]/g, ''));
      if (!dollars || dollars <= 0) {
        Alert.alert('Set a price', 'Enter a price for sell listings.');
        return;
      }
      priceCents = Math.round(dollars * 100);
    }

    setSubmitting(true);
    try {
      await marketplaceAPI.create({
        clothing_item_id: selectedId,
        listing_type: listingType,
        description: description.trim() || undefined,
        price_cents: priceCents,
        condition,
      });
      await onCreated();
      onClose();
    } catch (error) {
      const message = getApiErrorMessage(error, 'Could not create listing.');
      if (message.toLowerCase().includes('already listed')) {
        Alert.alert(
          'Already listed',
          'This item is already on Pass it on. Open My listings to manage it.',
        );
      } else {
        Alert.alert('Error', message);
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Modal visible={visible} animationType="slide" onRequestClose={onClose}>
      <View style={styles.container}>
        <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
          <Text style={styles.title}>List from closet</Text>
          <Text style={styles.subtitle}>
            Sell or gift pieces you do not need. Buyers reach you by email — no in-app chat yet.
          </Text>

          <Text style={styles.sectionLabel}>Pick item</Text>
          {loading ? (
            <Text style={styles.hint}>Loading closet…</Text>
          ) : available.length === 0 ? (
            <Text style={styles.hint}>No unlisted items — add more to your closet first.</Text>
          ) : (
            <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.itemRow}>
              {available.map((item) => {
                const uri = mediaUrl(item.thumbnail_url ?? item.image_url);
                const active = selectedId === item.id;
                return (
                  <Pressable
                    key={item.id}
                    style={[styles.itemTile, active && styles.itemTileActive]}
                    onPress={() => setSelectedId(item.id)}
                  >
                    {uri ? (
                      <Image source={{ uri }} style={styles.itemImage} resizeMode="cover" />
                    ) : (
                      <View style={styles.itemPlaceholder}>
                        <Text>👕</Text>
                      </View>
                    )}
                    <Text style={styles.itemName} numberOfLines={2}>
                      {item.name}
                    </Text>
                  </Pressable>
                );
              })}
            </ScrollView>
          )}

          <Text style={styles.sectionLabel}>Listing type</Text>
          <View style={styles.typeRow}>
            {(['sell', 'gift'] as ListingType[]).map((type) => (
              <Pressable
                key={type}
                style={[styles.typePill, listingType === type && styles.typePillActive]}
                onPress={() => setListingType(type)}
              >
                <Text style={[styles.typeText, listingType === type && styles.typeTextActive]}>
                  {type === 'sell' ? 'Sell' : 'Gift'}
                </Text>
              </Pressable>
            ))}
          </View>

          {listingType === 'sell' ? (
            <TextInput
              style={styles.input}
              placeholder="Price (USD)"
              placeholderTextColor={THEME.utility.textMuted}
              keyboardType="decimal-pad"
              value={price}
              onChangeText={setPrice}
            />
          ) : null}

          <Text style={styles.sectionLabel}>Condition</Text>
          <View style={styles.typeRow}>
            {CONDITIONS.map((c) => (
              <Pressable
                key={c}
                style={[styles.typePill, condition === c && styles.typePillActive]}
                onPress={() => setCondition(c)}
              >
                <Text style={[styles.typeText, condition === c && styles.typeTextActive]}>
                  {c.replace('_', ' ')}
                </Text>
              </Pressable>
            ))}
          </View>

          <TextInput
            style={[styles.input, styles.textArea]}
            placeholder="Description (optional)"
            placeholderTextColor={THEME.utility.textMuted}
            multiline
            value={description}
            onChangeText={setDescription}
          />
        </ScrollView>

        <View style={styles.actions}>
          <Button title="Cancel" variant="secondary" onPress={onClose} />
          <Button title="List item" loading={submitting} onPress={handleSubmit} />
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: THEME.utility.background },
  content: { padding: 22, paddingBottom: 12, gap: 10 },
  title: { ...utilityTitle(24), textAlign: 'left' },
  subtitle: { fontSize: 14, lineHeight: 20, color: THEME.utility.textMuted },
  sectionLabel: {
    marginTop: 8,
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 0.8,
    textTransform: 'uppercase',
    color: THEME.utility.textMuted,
  },
  hint: { fontSize: 14, color: THEME.utility.textMuted, paddingVertical: 12 },
  itemRow: { gap: 10, paddingVertical: 8 },
  itemTile: {
    width: 96,
    borderRadius: 14,
    overflow: 'hidden',
    borderWidth: 2,
    borderColor: 'transparent',
    backgroundColor: THEME.utility.surface,
    ...SHADOW.soft,
  },
  itemTileActive: { borderColor: THEME.brand.accent },
  itemImage: { width: '100%', height: 110, backgroundColor: THEME.editorial.pill },
  itemPlaceholder: {
    height: 110,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: THEME.editorial.pill,
  },
  itemName: {
    fontSize: 11,
    fontWeight: '600',
    padding: 8,
    color: THEME.utility.text,
    minHeight: 44,
  },
  typeRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  typePill: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: THEME.utility.surfaceMuted,
    borderWidth: 1,
    borderColor: THEME.utility.border,
  },
  typePillActive: { backgroundColor: THEME.brand.accent, borderColor: THEME.brand.accent },
  typeText: { fontSize: 13, color: THEME.utility.text, textTransform: 'capitalize' },
  typeTextActive: { color: '#fff', fontWeight: '700' },
  input: {
    borderWidth: 1,
    borderColor: THEME.utility.border,
    borderRadius: 14,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 15,
    color: THEME.utility.text,
    backgroundColor: THEME.utility.surface,
  },
  textArea: { minHeight: 88, textAlignVertical: 'top' },
  actions: {
    flexDirection: 'row',
    gap: 10,
    paddingHorizontal: 22,
    paddingBottom: 28,
    paddingTop: 8,
  },
});
