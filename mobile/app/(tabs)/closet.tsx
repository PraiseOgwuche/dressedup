import React, { useCallback, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  FlatList,
  Image,
  Modal,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useFocusEffect } from 'expo-router';
import * as ImagePicker from 'expo-image-picker';

import { COLORS, mediaUrl, TAXONOMY } from '../../constants/config';
import { THEME, SHADOW, utilityTitle } from '../../constants/theme';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { ChipSelect } from '../../components/ui/ChipSelect';
import { closetAPI } from '../../services/api';
import { getApiErrorMessage } from '../../services/errors';
import { useClosetStore } from '../../store/closetStore';
import { ClosetItem, DraftItem } from '../../types';

const LOW_CONFIDENCE = 0.8;
const BATCH_LIMIT = 15;

type QueueEntry = { previewUri: string; imageUrl: string; thumbnailUrl: string; draft: DraftItem };

const wearStatusText = (item: ClosetItem): string => {
  const state = item.is_clean ? 'Clean' : 'In the hamper';
  const limit = item.effective_wear_limit;
  if (limit == null) {
    return `${state} • worn ${item.times_worn}× • not laundered`;
  }
  return `${state} • worn ${item.times_worn}× • ${item.wears_since_wash}/${limit} wears before wash`;
};

type FormState = {
  name: string;
  category: string;
  subcategory: string;
  brand: string;
  productName: string;
  color: string;
  material: string;
  size: string;
  pattern: string;
  formality: string;
  occasion: string[];
  weatherTag: string[];
  seasons: string[];
  isClean: boolean;
};

const EMPTY_FORM: FormState = {
  name: '',
  category: '',
  subcategory: '',
  brand: '',
  productName: '',
  color: '',
  material: '',
  size: '',
  pattern: '',
  formality: '',
  occasion: [],
  weatherTag: [],
  seasons: [],
  isClean: true,
};

export default function ClosetScreen() {
  const {
    items,
    laundry,
    isLoading,
    fetchItems,
    fetchLaundry,
    createItem,
    updateItem,
    deleteItem,
    wearItem,
    washItem,
    soilItem,
    washAll,
  } = useClosetStore();

  const [isFormOpen, setIsFormOpen] = useState(false);
  const [isIngesting, setIsIngesting] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);

  // Image + AI provenance carried from ingestion into the confirm form.
  const [imagePreview, setImagePreview] = useState<string | undefined>(undefined);
  const [imageUrl, setImageUrl] = useState<string | undefined>(undefined);
  const [thumbnailUrl, setThumbnailUrl] = useState<string | undefined>(undefined);
  const [source, setSource] = useState('manual');
  const [confidence, setConfidence] = useState<Record<string, number>>({});
  // AI-detected hex carried through (powers color matching) but not directly edited.
  const [colorHex, setColorHex] = useState<string | undefined>(undefined);

  // Bulk-scan review queue: confirm/skip drafts one at a time.
  const [queue, setQueue] = useState<QueueEntry[]>([]);
  const [queueIndex, setQueueIndex] = useState(0);
  const [queueSource, setQueueSource] = useState<'batch' | 'multi' | 'receipt' | null>(null);
  const inQueue = queue.length > 0;
  const [receiptContext, setReceiptContext] = useState<{ merchant?: string; purchase_date?: string }>({});
  const [receiptMeta, setReceiptMeta] = useState<{
    sku?: string;
    price?: number;
    purchase_date?: string;
    merchant?: string;
  }>({});

  const [categoryFilter, setCategoryFilter] = useState('');
  const [cleanFilter, setCleanFilter] = useState<'all' | 'clean' | 'dirty'>('all');
  const [searchQuery, setSearchQuery] = useState('');

  useFocusEffect(
    useCallback(() => {
      fetchItems();
      fetchLaundry();
    }, [fetchItems, fetchLaundry]),
  );

  const editingItem = editingId ? items.find((i) => i.id === editingId) : undefined;

  const runItemAction = async (action: () => Promise<void>, failure: string) => {
    try {
      await action();
      setIsFormOpen(false);
      resetForm();
    } catch (error: any) {
      Alert.alert('Error', getApiErrorMessage(error, failure));
    }
  };

  const handleWashAll = () => {
    Alert.alert('Did laundry?', 'Mark everything in the hamper as clean and ready?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Yes, all clean',
        onPress: async () => {
          try {
            await washAll();
          } catch (error: any) {
            Alert.alert('Error', getApiErrorMessage(error, 'Could not update laundry.'));
          }
        },
      },
    ]);
  };

  const cleanCount = useMemo(() => items.filter((i) => i.is_clean).length, [items]);

  const filteredItems = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    return items.filter((item) => {
      if (categoryFilter && item.category !== categoryFilter) return false;
      if (cleanFilter === 'clean' && !item.is_clean) return false;
      if (cleanFilter === 'dirty' && item.is_clean) return false;
      if (!q) return true;
      const haystack = [item.name, item.brand, item.category, item.subcategory, item.color]
        .filter(Boolean)
        .join(' ')
        .toLowerCase();
      return haystack.includes(q);
    });
  }, [items, categoryFilter, cleanFilter, searchQuery]);

  const setField = (key: keyof FormState, value: string | boolean | string[]) =>
    setForm((prev) => ({ ...prev, [key]: value }));

  // Single-select chips: tap selected to clear (optional fields).
  const selectOne = (key: keyof FormState, value: string) =>
    setForm((prev) => ({ ...prev, [key]: prev[key] === value ? '' : value }));

  // Multi-select chips (occasion / weather / seasons): toggle membership.
  const toggleMulti = (key: 'occasion' | 'weatherTag' | 'seasons', value: string) =>
    setForm((prev) => {
      const current = prev[key];
      return {
        ...prev,
        [key]: current.includes(value)
          ? current.filter((v) => v !== value)
          : [...current, value],
      };
    });

  const lowConf = (field: string) =>
    source !== 'manual' && (confidence[field] === undefined || confidence[field] < LOW_CONFIDENCE);

  const label = (text: string, field: string) => (lowConf(field) ? `${text}  ⚠ check` : text);

  const resetForm = () => {
    setForm(EMPTY_FORM);
    setEditingId(null);
    setImagePreview(undefined);
    setImageUrl(undefined);
    setThumbnailUrl(undefined);
    setSource('manual');
    setConfidence({});
    setColorHex(undefined);
    setReceiptContext({});
    setReceiptMeta({});
  };

  const applyDraft = (
    draft: DraftItem,
    serverImage: string,
    serverThumb: string,
    context?: { merchant?: string; purchase_date?: string },
  ) => {
    const merchant = context?.merchant ?? receiptContext.merchant;
    const purchaseDate = draft.purchase_date ?? context?.purchase_date ?? receiptContext.purchase_date;
    setForm({
      name: draft.name ?? '',
      category: draft.category ?? '',
      subcategory: draft.subcategory ?? '',
      brand: draft.brand ?? '',
      productName: draft.product_name ?? '',
      color: draft.color ?? '',
      material: draft.material ?? '',
      size: draft.size ?? '',
      pattern: draft.pattern ?? '',
      formality: draft.formality ?? '',
      occasion: draft.occasion ?? [],
      weatherTag: draft.weather_tag ?? [],
      seasons: draft.seasons ?? [],
      isClean: true,
    });
    setColorHex(draft.color_hex ?? undefined);
    setImageUrl(serverImage);
    setThumbnailUrl(serverThumb);
    setSource(draft.source ?? 'photo');
    setConfidence(draft.confidence ?? {});
    setReceiptMeta({
      sku: draft.sku ?? undefined,
      price: draft.price ?? undefined,
      purchase_date: purchaseDate,
      merchant,
    });
  };

  const pickImage = async (fromCamera: boolean): Promise<ImagePicker.ImagePickerAsset | null> => {
    const permission = fromCamera
      ? await ImagePicker.requestCameraPermissionsAsync()
      : await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permission.granted) {
      Alert.alert('Permission needed', 'Enable camera/photo access in Settings to add items by photo.');
      return null;
    }
    const result = fromCamera
      ? await ImagePicker.launchCameraAsync({ quality: 0.7 })
      : await ImagePicker.launchImageLibraryAsync({ quality: 0.7 });
    if (result.canceled || !result.assets?.length) return null;
    return result.assets[0];
  };

  const runIngestion = async (fromCamera: boolean) => {
    const garment = await pickImage(fromCamera);
    if (!garment) return;

    const addLabel = await new Promise<boolean>((resolve) => {
      Alert.alert(
        'Add a care label?',
        'Photograph the inside tag so we can capture brand and material.',
        [
          { text: 'Skip', style: 'cancel', onPress: () => resolve(false) },
          { text: 'Add label', onPress: () => resolve(true) },
        ],
      );
    });

    let labelAsset: ImagePicker.ImagePickerAsset | null = null;
    if (addLabel) {
      labelAsset = await pickImage(fromCamera);
    }

    setIsIngesting(true);
    try {
      const result = await closetAPI.ingest(
        { uri: garment.uri, name: garment.fileName, mimeType: garment.mimeType },
        labelAsset ? { uri: labelAsset.uri, name: labelAsset.fileName, mimeType: labelAsset.mimeType } : null,
      );
      resetForm();
      setImagePreview(garment.uri);
      applyDraft(result.draft, result.image_url, result.thumbnail_url);
      setIsFormOpen(true);
    } catch (error: any) {
      Alert.alert('Scan failed', getApiErrorMessage(error, 'Could not analyze that photo.'));
    } finally {
      setIsIngesting(false);
    }
  };

  const loadQueueItem = (
    entries: QueueEntry[],
    index: number,
    source: 'batch' | 'multi' | 'receipt',
    context?: { merchant?: string; purchase_date?: string },
  ) => {
    const entry = entries[index];
    resetForm();
    setQueue(entries);
    setQueueIndex(index);
    setQueueSource(source);
    setImagePreview(entry.previewUri);
    applyDraft(entry.draft, entry.imageUrl, entry.thumbnailUrl, context);
    setIsFormOpen(true);
  };

  const finishQueue = () => {
    setQueue([]);
    setQueueIndex(0);
    setQueueSource(null);
    setIsFormOpen(false);
    resetForm();
  };

  const advanceQueue = () => {
    if (queueIndex < queue.length - 1 && queueSource) {
      loadQueueItem(queue, queueIndex + 1, queueSource, receiptContext);
    } else {
      finishQueue();
    }
  };

  const runBatchIngestion = async () => {
    const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permission.granted) {
      Alert.alert('Permission needed', 'Enable photo access in Settings to scan items.');
      return;
    }
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsMultipleSelection: true,
      selectionLimit: BATCH_LIMIT,
      quality: 0.7,
    });
    if (result.canceled || !result.assets?.length) return;

    const assets = result.assets.slice(0, BATCH_LIMIT);
    setIsIngesting(true);
    try {
      const batch = await closetAPI.ingestBatch(
        assets.map((a) => ({ uri: a.uri, name: a.fileName, mimeType: a.mimeType })),
      );
      const entries: QueueEntry[] = [];
      batch.entries.forEach((entry, i) => {
        if (entry.result) {
          entries.push({
            previewUri: assets[i]?.uri ?? mediaUrl(entry.result.image_url) ?? '',
            imageUrl: entry.result.image_url,
            thumbnailUrl: entry.result.thumbnail_url,
            draft: entry.result.draft,
          });
        }
      });
      const failed = assets.length - entries.length;
      if (!entries.length) {
        Alert.alert('Scan failed', 'None of those photos could be analyzed.');
        return;
      }
      if (failed > 0) {
        Alert.alert('Heads up', `${failed} photo(s) couldn’t be analyzed and were skipped.`);
      }
      loadQueueItem(entries, 0, 'batch');
    } catch (error: any) {
      Alert.alert('Scan failed', getApiErrorMessage(error, 'Could not analyze those photos.'));
    } finally {
      setIsIngesting(false);
    }
  };

  const runMultiIngestion = async (fromCamera: boolean) => {
    const garment = await pickImage(fromCamera);
    if (!garment) return;

    setIsIngesting(true);
    try {
      const result = await closetAPI.ingestMulti({
        uri: garment.uri,
        name: garment.fileName,
        mimeType: garment.mimeType,
      });
      const entries: QueueEntry[] = result.entries.map((entry) => ({
        previewUri: garment.uri,
        imageUrl: entry.image_url,
        thumbnailUrl: entry.thumbnail_url,
        draft: entry.draft,
      }));
      if (!entries.length) {
        Alert.alert('Scan failed', 'No items were detected in that photo.');
        return;
      }
      Alert.alert(
        'Items found',
        `Detected ${entries.length} item${entries.length === 1 ? '' : 's'} — review each one.`,
      );
      loadQueueItem(entries, 0, 'multi');
    } catch (error: any) {
      Alert.alert('Scan failed', getApiErrorMessage(error, 'Could not analyze that flat-lay.'));
    } finally {
      setIsIngesting(false);
    }
  };

  const runReceiptIngestion = async (fromCamera: boolean) => {
    const receipt = await pickImage(fromCamera);
    if (!receipt) return;

    setIsIngesting(true);
    try {
      const result = await closetAPI.ingestReceipt({
        uri: receipt.uri,
        name: receipt.fileName,
        mimeType: receipt.mimeType,
      });
      const entries: QueueEntry[] = result.entries.map((entry) => ({
        previewUri: receipt.uri,
        imageUrl: entry.image_url,
        thumbnailUrl: entry.thumbnail_url,
        draft: entry.draft,
      }));
      if (!entries.length) {
        Alert.alert('No apparel found', 'We could not find clothing lines on that receipt.');
        return;
      }
      const ctx = {
        merchant: result.merchant ?? undefined,
        purchase_date: result.purchase_date ?? undefined,
      };
      setReceiptContext(ctx);
      Alert.alert(
        'Receipt scanned',
        `${entries.length} item${entries.length === 1 ? '' : 's'} from ${result.merchant ?? 'the receipt'} — review each one.`,
      );
      loadQueueItem(entries, 0, 'receipt', ctx);
    } catch (error: any) {
      Alert.alert('Scan failed', getApiErrorMessage(error, 'Could not read that receipt.'));
    } finally {
      setIsIngesting(false);
    }
  };

  const runLabelIngestion = async (fromCamera: boolean) => {
    const label = await pickImage(fromCamera);
    if (!label) return;

    setIsIngesting(true);
    try {
      const result = await closetAPI.ingestLabel({
        uri: label.uri,
        name: label.fileName,
        mimeType: label.mimeType,
      });
      resetForm();
      setImagePreview(label.uri);
      applyDraft(result.draft, result.image_url, result.thumbnail_url);
      setIsFormOpen(true);
    } catch (error: any) {
      Alert.alert('Scan failed', getApiErrorMessage(error, 'Could not read that label.'));
    } finally {
      setIsIngesting(false);
    }
  };

  const openAddMenu = () => {
    Alert.alert('Add to closet', 'How would you like to add items?', [
      { text: 'Take photo (1 item)', onPress: () => runIngestion(true) },
      { text: 'Choose photo (1 item)', onPress: () => runIngestion(false) },
      { text: 'Scan receipt', onPress: () => runReceiptIngestion(false) },
      { text: 'Scan care label only', onPress: () => runLabelIngestion(false) },
      { text: 'Flat-lay scan (many in 1 photo)', onPress: () => runMultiIngestion(false) },
      { text: 'Scan many photos', onPress: () => runBatchIngestion() },
      { text: 'Add manually', onPress: () => { resetForm(); setIsFormOpen(true); } },
      { text: 'Cancel', style: 'cancel' },
    ]);
  };

  const openEdit = (item: ClosetItem) => {
    resetForm();
    setEditingId(item.id);
    setForm({
      name: item.name,
      category: item.category,
      subcategory: item.subcategory ?? '',
      brand: item.brand ?? '',
      productName: item.product_name ?? '',
      color: item.color ?? '',
      material: item.material ?? '',
      size: item.size ?? '',
      pattern: item.pattern ?? '',
      formality: item.formality ?? '',
      occasion: item.occasion ?? [],
      weatherTag: item.weather_tag ?? [],
      seasons: item.seasons ?? [],
      isClean: item.is_clean,
    });
    setColorHex(item.color_hex ?? undefined);
    setImageUrl(item.image_url ?? undefined);
    setThumbnailUrl(item.thumbnail_url ?? undefined);
    setImagePreview(mediaUrl(item.image_url));
    setIsFormOpen(true);
  };

  const handleSave = async () => {
    if (!form.name.trim() || !form.category.trim()) {
      Alert.alert('Missing fields', 'Name and category are required.');
      return;
    }
    const aiMetadata =
      receiptMeta.sku || receiptMeta.price != null || receiptMeta.merchant || receiptMeta.purchase_date
        ? {
            ...(receiptMeta.sku ? { sku: receiptMeta.sku } : {}),
            ...(receiptMeta.price != null ? { price: receiptMeta.price } : {}),
            ...(receiptMeta.merchant ? { merchant: receiptMeta.merchant } : {}),
            ...(receiptMeta.purchase_date ? { purchase_date: receiptMeta.purchase_date } : {}),
          }
        : undefined;
    const payload = {
      name: form.name.trim(),
      category: form.category.trim().toLowerCase(),
      subcategory: form.subcategory || undefined,
      brand: form.brand.trim() || undefined,
      product_name: form.productName.trim() || undefined,
      color: form.color.trim() || undefined,
      color_hex: colorHex,
      material: form.material.trim() || undefined,
      size: form.size.trim() || undefined,
      pattern: form.pattern || undefined,
      formality: form.formality || undefined,
      occasion: form.occasion.length ? form.occasion : undefined,
      weather_tag: form.weatherTag.length ? form.weatherTag : undefined,
      seasons: form.seasons.length ? form.seasons : undefined,
      is_clean: form.isClean,
      image_url: imageUrl,
      thumbnail_url: thumbnailUrl,
      source,
      needs_review: false,
      ai_metadata: aiMetadata,
    };
    try {
      if (editingId) {
        await updateItem(editingId, payload);
      } else {
        await createItem({ ...payload, confidence });
      }
      if (inQueue) {
        advanceQueue();
      } else {
        setIsFormOpen(false);
        resetForm();
      }
    } catch (error: any) {
      Alert.alert('Error', getApiErrorMessage(error, 'Could not save this item.'));
    }
  };

  const handleCancel = () => {
    if (inQueue) {
      finishQueue();
    } else {
      setIsFormOpen(false);
    }
  };

  const handleDelete = (item: ClosetItem) => {
    Alert.alert('Delete item', `Remove "${item.name}" from your closet?`, [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete',
        style: 'destructive',
        onPress: async () => {
          try {
            await deleteItem(item.id);
          } catch (error: any) {
            Alert.alert('Error', getApiErrorMessage(error, 'Could not delete this item.'));
          }
        },
      },
    ]);
  };

  const renderItem = ({ item }: { item: ClosetItem }) => {
    const thumb = mediaUrl(item.thumbnail_url ?? item.image_url);
    return (
      <Pressable style={styles.gridCard} onPress={() => openEdit(item)}>
        <View style={styles.thumbWrap}>
          {thumb ? (
            <Image source={{ uri: thumb }} style={styles.thumb} resizeMode="cover" />
          ) : (
            <View style={styles.thumbPlaceholder}>
              <Text style={styles.thumbEmoji}>👕</Text>
            </View>
          )}
          {item.needs_review ? <Text style={styles.reviewBadge}>Review</Text> : null}
          {!item.is_clean ? <Text style={styles.dirtyBadge}>Dirty</Text> : null}
        </View>
        <Text style={styles.gridName} numberOfLines={1}>{item.name}</Text>
        <Text style={styles.gridMeta} numberOfLines={1}>
          {item.brand ? `${item.brand} • ` : ''}{item.category}
        </Text>
      </Pressable>
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Closet</Text>
        <Text style={styles.subtitle}>
          {items.length
            ? `${filteredItems.length} piece${filteredItems.length === 1 ? '' : 's'} · ${cleanCount} clean`
            : 'Snap a flat-lay or add items to get started'}
        </Text>
      </View>
      <View style={styles.toolbar}>
        <Button title="+ Add" onPress={openAddMenu} />
      </View>

      {items.length > 0 ? (
        <View style={styles.filters}>
          <Input
            label="Search"
            value={searchQuery}
            onChangeText={setSearchQuery}
            placeholder="Name, brand, color…"
          />
          <ChipSelect
            label="Category"
            options={TAXONOMY.categories}
            selected={categoryFilter}
            onSelect={(v) => setCategoryFilter((prev) => (prev === v ? '' : v))}
          />
          <ChipSelect
            label="Laundry"
            options={['all', 'clean', 'dirty']}
            selected={cleanFilter}
            onSelect={(v) => setCleanFilter(v as 'all' | 'clean' | 'dirty')}
          />
        </View>
      ) : null}

      {laundry ? (
        <View style={[styles.laundryBanner, laundry.laundry_due && styles.laundryBannerDue]}>
          <Text style={[styles.laundryText, laundry.laundry_due && styles.laundryTextDue]} numberOfLines={2}>
            {laundry.laundry_due ? '🧺 ' : '✓ '}{laundry.message}
          </Text>
          {laundry.dirty_count > 0 ? (
            <Pressable onPress={handleWashAll} style={styles.laundryActionBtn}>
              <Text style={styles.laundryActionText}>I did laundry</Text>
            </Pressable>
          ) : null}
        </View>
      ) : null}

      <FlatList
        data={filteredItems}
        keyExtractor={(item) => item.id.toString()}
        renderItem={renderItem}
        numColumns={2}
        columnWrapperStyle={filteredItems.length ? styles.row : undefined}
        contentContainerStyle={filteredItems.length ? styles.listContent : styles.emptyContainer}
        refreshControl={<RefreshControl refreshing={isLoading} onRefresh={fetchItems} />}
        ListEmptyComponent={
          items.length ? (
            <View style={styles.emptyState}>
              <Text style={styles.emptyEmoji}>🔍</Text>
              <Text style={styles.emptyText}>No matches</Text>
              <Text style={styles.emptySubtext}>Try clearing filters or search.</Text>
            </View>
          ) : (
            <View style={styles.emptyState}>
              <Text style={styles.emptyEmoji}>📸</Text>
              <Text style={styles.emptyText}>Your closet is empty</Text>
              <Text style={styles.emptySubtext}>
                Lay clothes flat and scan one photo for several items, or add them one at a time.
              </Text>
              <Button title="Flat-lay scan" onPress={() => runMultiIngestion(false)} style={styles.emptyBtn} />
              <Button title="Add one item" variant="outline" onPress={() => runIngestion(false)} style={styles.emptyBtn} />
            </View>
          )
        }
      />

      {isIngesting ? (
        <View style={styles.overlay}>
          <ActivityIndicator size="large" color="#fff" />
          <Text style={styles.overlayText}>Finding items in your photo…</Text>
        </View>
      ) : null}

      <Modal visible={isFormOpen} animationType="slide" onRequestClose={handleCancel}>
        <SafeAreaView style={styles.modalContainer}>
          <ScrollView contentContainerStyle={styles.modalContent}>
            <Text style={styles.modalTitle}>
              {editingId ? 'Edit item' : source !== 'manual' ? 'Confirm item' : 'Add item'}
            </Text>
            {inQueue ? (
              <Text style={styles.queueProgress}>
                {queueSource === 'multi'
                  ? 'Flat-lay'
                  : queueSource === 'receipt'
                    ? 'Receipt'
                    : 'Batch'}{' '}
                — item {queueIndex + 1} of {queue.length}
              </Text>
            ) : null}

            {imagePreview ? <Image source={{ uri: imagePreview }} style={styles.preview} resizeMode="cover" /> : null}
            {source !== 'manual' && !editingId ? (
              <Text style={styles.aiNote}>AI filled these in — fields marked ⚠ are worth a check.</Text>
            ) : null}

            {editingItem ? (
              <View style={styles.wearCard}>
                <Text style={styles.wearStatus}>{wearStatusText(editingItem)}</Text>
                <View style={styles.wearActions}>
                  <Button
                    title="Wore it today"
                    variant="outline"
                    onPress={() => runItemAction(() => wearItem(editingItem.id), 'Could not record wear.')}
                    style={styles.wearBtn}
                  />
                  {editingItem.is_clean ? (
                    <Button
                      title="Mark dirty"
                      variant="secondary"
                      onPress={() => runItemAction(() => soilItem(editingItem.id), 'Could not update.')}
                      style={styles.wearBtn}
                    />
                  ) : (
                    <Button
                      title="Mark clean"
                      variant="secondary"
                      onPress={() => runItemAction(() => washItem(editingItem.id), 'Could not update.')}
                      style={styles.wearBtn}
                    />
                  )}
                </View>
              </View>
            ) : null}

            <Input label={label('Name', 'name')} value={form.name} onChangeText={(v) => setField('name', v)} placeholder="Black crewneck tee" />
            <ChipSelect
              label={label('Category', 'category')}
              options={TAXONOMY.categories}
              selected={form.category}
              onSelect={(v) => selectOne('category', v)}
            />
            {TAXONOMY.subcategories[form.category]?.length ? (
              <ChipSelect
                label={label('Subcategory', 'subcategory')}
                options={TAXONOMY.subcategories[form.category]}
                selected={form.subcategory}
                onSelect={(v) => selectOne('subcategory', v)}
              />
            ) : null}
            <Input label={label('Brand', 'brand')} value={form.brand} onChangeText={(v) => setField('brand', v)} placeholder="Uniqlo" />
            <Input
              label={label('Product name', 'product_name')}
              value={form.productName}
              onChangeText={(v) => setField('productName', v)}
              placeholder="Slim Fit Chino Pants"
            />
            {receiptMeta.price != null || receiptMeta.sku ? (
              <Text style={styles.receiptHint}>
                {receiptMeta.price != null ? `$${receiptMeta.price.toFixed(2)}` : ''}
                {receiptMeta.price != null && receiptMeta.sku ? ' · ' : ''}
                {receiptMeta.sku ? `SKU ${receiptMeta.sku}` : ''}
              </Text>
            ) : null}
            <Input label={label('Color', 'color')} value={form.color} onChangeText={(v) => setField('color', v)} placeholder="black" />
            <Input label={label('Material', 'material')} value={form.material} onChangeText={(v) => setField('material', v)} placeholder="100% cotton" />
            <Input label={label('Size', 'size')} value={form.size} onChangeText={(v) => setField('size', v)} placeholder="M" />
            <ChipSelect
              label={label('Pattern', 'pattern')}
              options={TAXONOMY.patterns}
              selected={form.pattern}
              onSelect={(v) => selectOne('pattern', v)}
            />
            <ChipSelect
              label={label('Formality', 'formality')}
              options={TAXONOMY.formality}
              selected={form.formality}
              onSelect={(v) => selectOne('formality', v)}
            />
            <ChipSelect
              label={label('Occasion', 'occasion')}
              hint="Pick all that apply."
              options={TAXONOMY.occasions}
              selected={form.occasion}
              onSelect={(v) => toggleMulti('occasion', v)}
              multiple
            />
            <ChipSelect
              label={label('Weather', 'weather_tag')}
              hint="Pick all that apply."
              options={TAXONOMY.weather}
              selected={form.weatherTag}
              onSelect={(v) => toggleMulti('weatherTag', v)}
              multiple
            />
            <ChipSelect
              label={label('Seasons', 'seasons')}
              hint="Pick all that apply — used to match outfits to the weather."
              options={TAXONOMY.seasons}
              selected={form.seasons}
              onSelect={(v) => toggleMulti('seasons', v)}
              multiple
            />

            <View style={styles.switchRow}>
              <Text style={styles.switchLabel}>Is clean</Text>
              <Switch value={form.isClean} onValueChange={(v) => setField('isClean', v)} />
            </View>

            <View style={styles.modalActions}>
              <Button
                title={inQueue ? 'Stop' : 'Cancel'}
                variant="outline"
                onPress={handleCancel}
                style={styles.modalAction}
              />
              <Button
                title={
                  inQueue
                    ? queueIndex < queue.length - 1 ? 'Save & Next' : 'Save & Finish'
                    : editingId ? 'Save Changes' : 'Save to Closet'
                }
                onPress={handleSave}
                style={styles.modalAction}
              />
            </View>
            {inQueue ? (
              <Button title="Skip this item" variant="secondary" onPress={advanceQueue} />
            ) : null}
            {editingId ? (
              <Button title="Delete item" variant="secondary" onPress={() => { setIsFormOpen(false); const item = items.find((i) => i.id === editingId); if (item) handleDelete(item); }} />
            ) : null}
          </ScrollView>
        </SafeAreaView>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: THEME.utility.background },
  header: { paddingHorizontal: 22, paddingTop: 12, paddingBottom: 8 },
  title: { ...utilityTitle(28), textAlign: 'left' },
  subtitle: { fontSize: 14, color: THEME.utility.textMuted, marginTop: 4 },
  toolbar: { paddingHorizontal: 22, paddingBottom: 12 },
  filters: { paddingHorizontal: 22, paddingBottom: 8 },
  emptyBtn: { marginTop: 12, alignSelf: 'stretch' },
  laundryBanner: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    marginHorizontal: 22, marginBottom: 12, padding: 14, borderRadius: 14,
    backgroundColor: THEME.utility.surfaceMuted,
  },
  laundryBannerDue: { backgroundColor: '#FFF8EE' },
  laundryText: { flex: 1, fontSize: 13, color: THEME.utility.textMuted, fontWeight: '600' },
  laundryTextDue: { color: THEME.shared.warning },
  laundryActionBtn: {
    marginLeft: 10, paddingHorizontal: 12, paddingVertical: 6,
    borderRadius: 16, backgroundColor: THEME.utility.accent,
  },
  laundryActionText: { color: '#fff', fontSize: 12, fontWeight: '700' },
  wearCard: {
    backgroundColor: THEME.utility.surfaceMuted, borderRadius: 14, padding: 14, marginBottom: 16,
  },
  wearStatus: { fontSize: 13, color: THEME.utility.text, fontWeight: '600', marginBottom: 10 },
  wearActions: { flexDirection: 'row', gap: 10 },
  wearBtn: { flex: 1 },
  listContent: { paddingHorizontal: 18, paddingBottom: 40 },
  row: { gap: 14, marginBottom: 14 },
  emptyContainer: { flexGrow: 1, justifyContent: 'center', padding: 22 },
  emptyState: {
    alignItems: 'center',
    backgroundColor: THEME.utility.surfaceMuted,
    borderRadius: 20,
    padding: 28,
    ...SHADOW.soft,
  },
  emptyEmoji: { fontSize: 56, marginBottom: 12 },
  emptyText: { fontSize: 20, fontWeight: '700', color: THEME.utility.text, marginBottom: 8 },
  emptySubtext: { fontSize: 14, color: THEME.utility.textMuted, textAlign: 'center', lineHeight: 20 },
  gridCard: {
    flex: 1,
    backgroundColor: THEME.utility.surface,
    borderRadius: 16,
    padding: 8,
    borderWidth: 1,
    borderColor: THEME.utility.border,
    ...SHADOW.soft,
  },
  thumbWrap: {
    width: '100%',
    aspectRatio: 1,
    borderRadius: 12,
    overflow: 'hidden',
    backgroundColor: THEME.editorial.pill,
  },
  thumb: { width: '100%', height: '100%' },
  thumbPlaceholder: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  thumbEmoji: { fontSize: 48 },
  reviewBadge: {
    position: 'absolute', top: 8, left: 8, fontSize: 11, fontWeight: '700', color: '#fff',
    backgroundColor: COLORS.warning, paddingHorizontal: 8, paddingVertical: 4, borderRadius: 10, overflow: 'hidden',
  },
  dirtyBadge: {
    position: 'absolute', top: 8, right: 8, fontSize: 11, fontWeight: '700', color: '#fff',
    backgroundColor: COLORS.error, paddingHorizontal: 8, paddingVertical: 4, borderRadius: 10, overflow: 'hidden',
  },
  gridName: { marginTop: 8, fontSize: 13, fontWeight: '700', color: THEME.utility.text },
  gridMeta: { marginTop: 2, fontSize: 11, color: THEME.utility.textMuted },
  overlay: {
    ...StyleSheet.absoluteFillObject, backgroundColor: 'rgba(0,0,0,0.55)',
    alignItems: 'center', justifyContent: 'center', gap: 12,
  },
  overlayText: { color: '#fff', fontSize: 16, fontWeight: '600' },
  modalContainer: { flex: 1, backgroundColor: THEME.utility.background },
  modalContent: { padding: 22, paddingBottom: 40 },
  modalTitle: { ...utilityTitle(24), marginBottom: 16 },
  preview: { width: '100%', height: 220, borderRadius: 16, marginBottom: 12, backgroundColor: THEME.editorial.pill },
  aiNote: { fontSize: 13, color: THEME.utility.textMuted, marginBottom: 12 },
  receiptHint: { fontSize: 13, color: THEME.utility.textMuted, marginBottom: 12, marginTop: -4 },
  queueProgress: { fontSize: 13, color: THEME.brand.ink, fontWeight: '700', marginBottom: 12 },
  switchRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: 8, marginBottom: 20 },
  switchLabel: { fontSize: 16, color: THEME.utility.text, fontWeight: '600' },
  modalActions: { flexDirection: 'row', gap: 10, marginBottom: 12 },
  modalAction: { flex: 1 },
});
