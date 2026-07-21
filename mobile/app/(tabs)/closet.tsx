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
  TextInput,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useFocusEffect } from 'expo-router';
import * as ImagePicker from 'expo-image-picker';

import { mediaUrl, TAXONOMY } from '../../constants/config';
import { THEME, SHADOW, utilityTitle, FONTS } from '../../constants/theme';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { ChipSelect } from '../../components/ui/ChipSelect';
import { ClosetGridCard } from '../../components/closet/ClosetGridCard';
import { ClosetItemDetailSheet } from '../../components/closet/ClosetItemDetailSheet';
import { closetAPI } from '../../services/api';
import { getApiErrorMessage } from '../../services/errors';
import { useClosetStore } from '../../store/closetStore';
import { ClosetGapsResponse, ClosetItem, DraftItem } from '../../types';
import {
  CleanFilter,
  ClosetSort,
  filterAndSortCloset,
  uniqueSorted,
} from '../../utils/closetQuery';
import {
  ConfirmField,
  draftLooksSolid,
  fieldsNeedingCheck,
  formatAcceptedSummary,
  shouldUseSmartConfirm,
} from '../../utils/confirmFields';

const BATCH_LIMIT = 15;
const SORT_OPTIONS: { key: ClosetSort; label: string }[] = [
  { key: 'newest', label: 'Newest' },
  { key: 'least_worn', label: 'Least worn' },
  { key: 'needs_wash', label: 'Needs wash' },
];

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
  tags: string[];
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
  tags: [],
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
    replacePhoto,
    backfillCutouts,
    wearItem,
    washItem,
    soilItem,
    washAll,
  } = useClosetStore();

  const [isFormOpen, setIsFormOpen] = useState(false);
  const [isIngesting, setIsIngesting] = useState(false);
  const [replacingPhoto, setReplacingPhoto] = useState(false);
  const [busyItemId, setBusyItemId] = useState<number | null>(null);
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
  const [cleanFilter, setCleanFilter] = useState<CleanFilter>('all');
  const [colorFilter, setColorFilter] = useState('');
  const [brandFilter, setBrandFilter] = useState('');
  const [seasonFilter, setSeasonFilter] = useState('');
  const [formalityFilter, setFormalityFilter] = useState('');
  const [tagFilter, setTagFilter] = useState('');
  const [sort, setSort] = useState<ClosetSort>('newest');
  const [searchQuery, setSearchQuery] = useState('');
  const [showMoreFilters, setShowMoreFilters] = useState(false);
  const [improvingPhotos, setImprovingPhotos] = useState(false);
  const [detailItem, setDetailItem] = useState<ClosetItem | null>(null);
  const [gaps, setGaps] = useState<ClosetGapsResponse | null>(null);
  const [showAllFields, setShowAllFields] = useState(false);

  useFocusEffect(
    useCallback(() => {
      fetchItems();
      fetchLaundry();
      closetAPI
        .gaps()
        .then(setGaps)
        .catch(() => setGaps(null));
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
  const dirtyCount = useMemo(() => items.filter((i) => !i.is_clean).length, [items]);
  const reviewCount = useMemo(() => items.filter((i) => i.needs_review).length, [items]);
  const colorOptions = useMemo(() => uniqueSorted(items.map((i) => i.color)), [items]);
  const brandOptions = useMemo(() => uniqueSorted(items.map((i) => i.brand)), [items]);

  const filteredItems = useMemo(
    () =>
      filterAndSortCloset(items, {
        searchQuery,
        categoryFilter,
        cleanFilter,
        colorFilter,
        brandFilter,
        seasonFilter,
        formalityFilter,
        tagFilter,
        sort,
      }),
    [
      items,
      searchQuery,
      categoryFilter,
      cleanFilter,
      colorFilter,
      brandFilter,
      seasonFilter,
      formalityFilter,
      tagFilter,
      sort,
    ],
  );

  const needsCutoutCount = useMemo(
    () =>
      items.filter(
        (i) =>
          i.image_url &&
          (!i.thumbnail_url || i.thumbnail_url === i.image_url || !i.thumbnail_url.includes('/cutouts/')),
      ).length,
    [items],
  );

  const handleImprovePhotos = () => {
    Alert.alert(
      'Improve photos',
      needsCutoutCount
        ? `Generate clean cutouts for up to 20 items that still show the original photo (${needsCutoutCount} candidates).`
        : 'Your photos already look cleaned up. Run anyway?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Improve',
          onPress: async () => {
            setImprovingPhotos(true);
            try {
              const result = await backfillCutouts(20);
              Alert.alert(
                'Photos updated',
                result.updated
                  ? `Improved ${result.updated} photo${result.updated === 1 ? '' : 's'}${result.skipped ? ` · ${result.skipped} skipped` : ''}.`
                  : `No new cutouts yet${result.skipped ? ` (${result.skipped} skipped)` : ''}.`,
              );
            } catch (error: any) {
              Alert.alert('Error', getApiErrorMessage(error, 'Could not improve photos.'));
            } finally {
              setImprovingPhotos(false);
            }
          },
        },
      ],
    );
  };

  const clearExtraFilters = () => {
    setColorFilter('');
    setBrandFilter('');
    setSeasonFilter('');
    setFormalityFilter('');
    setTagFilter('');
  };

  const runQuickAction = async (itemId: number, action: () => Promise<void>, failure: string) => {
    setBusyItemId(itemId);
    try {
      await action();
    } catch (error: any) {
      Alert.alert('Error', getApiErrorMessage(error, failure));
    } finally {
      setBusyItemId(null);
    }
  };

  const setField = (key: keyof FormState, value: string | boolean | string[]) =>
    setForm((prev) => ({ ...prev, [key]: value }));

  // Single-select chips: tap selected to clear (optional fields).
  const selectOne = (key: keyof FormState, value: string) =>
    setForm((prev) => ({ ...prev, [key]: prev[key] === value ? '' : value }));

  // Multi-select chips (occasion / weather / seasons): toggle membership.
  const toggleMulti = (key: 'occasion' | 'weatherTag' | 'seasons' | 'tags', value: string) =>
    setForm((prev) => {
      const current = prev[key];
      return {
        ...prev,
        [key]: current.includes(value)
          ? current.filter((v) => v !== value)
          : [...current, value],
      };
    });

  const lowConf = (field: string) => {
    if (source === 'manual') return false;
    const score = confidence[field];
    if (typeof score === 'number') return score < 0.8;
    return false;
  };

  const label = (text: string, field: string) => (lowConf(field) ? `${text}  ⚠ check` : text);

  const confirmValues = useMemo(
    () => ({
      name: form.name,
      category: form.category,
      subcategory: form.subcategory,
      brand: form.brand,
      product_name: form.productName,
      color: form.color,
      material: form.material,
      size: form.size,
      pattern: form.pattern,
      formality: form.formality,
      occasion: form.occasion,
      weather_tag: form.weatherTag,
      seasons: form.seasons,
    }),
    [form],
  );

  const smartConfirm = shouldUseSmartConfirm(source, Boolean(editingId));
  const checkFields = useMemo(
    () => (smartConfirm ? fieldsNeedingCheck(confidence, confirmValues, source) : []),
    [smartConfirm, confidence, confirmValues, source],
  );
  const acceptedSummary = useMemo(
    () => (smartConfirm ? formatAcceptedSummary(confirmValues, checkFields) : ''),
    [smartConfirm, confirmValues, checkFields],
  );
  const looksSolid = useMemo(
    () => (smartConfirm ? draftLooksSolid(confidence, confirmValues, source) : false),
    [smartConfirm, confidence, confirmValues, source],
  );

  const showField = (field: ConfirmField) => {
    if (!smartConfirm || showAllFields) return true;
    if (field === 'name' || field === 'category') return true;
    return checkFields.includes(field);
  };

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
    setShowAllFields(false);
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
      tags: [],
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
        previewUri: mediaUrl(entry.thumbnail_url || entry.image_url) || garment.uri,
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
      tags: item.tags ?? [],
      isClean: item.is_clean,
    });
    setColorHex(item.color_hex ?? undefined);
    setImageUrl(item.image_url ?? undefined);
    setThumbnailUrl(item.thumbnail_url ?? undefined);
    setImagePreview(mediaUrl(item.image_url));
    setDetailItem(null);
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
      tags: form.tags,
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

  const handleReplacePhoto = async (fromCamera: boolean) => {
    if (!editingId) return;
    const asset = await pickImage(fromCamera);
    if (!asset) return;
    setReplacingPhoto(true);
    try {
      await replacePhoto(editingId, {
        uri: asset.uri,
        name: asset.fileName,
        mimeType: asset.mimeType,
      });
      const refreshed = useClosetStore.getState().items.find((i) => i.id === editingId);
      if (refreshed) {
        setImageUrl(refreshed.image_url ?? undefined);
        setThumbnailUrl(refreshed.thumbnail_url ?? undefined);
        setImagePreview(mediaUrl(refreshed.thumbnail_url ?? refreshed.image_url) ?? asset.uri);
      } else {
        setImagePreview(asset.uri);
      }
    } catch (error: any) {
      Alert.alert('Photo replace failed', getApiErrorMessage(error, 'Could not update that photo.'));
    } finally {
      setReplacingPhoto(false);
    }
  };

  const openReplacePhotoMenu = () => {
    Alert.alert('Replace photo', 'Choose a new photo for this item.', [
      { text: 'Take photo', onPress: () => handleReplacePhoto(true) },
      { text: 'Choose from library', onPress: () => handleReplacePhoto(false) },
      { text: 'Cancel', style: 'cancel' },
    ]);
  };

  const renderItem = ({ item }: { item: ClosetItem }) => (
    <ClosetGridCard
      item={item}
      onPress={() => setDetailItem(item)}
      busy={busyItemId === item.id}
      onWear={() => runQuickAction(item.id, () => wearItem(item.id), 'Could not record wear.')}
      onSoilOrWash={() =>
        runQuickAction(
          item.id,
          () => (item.is_clean ? soilItem(item.id) : washItem(item.id)),
          'Could not update laundry status.',
        )
      }
      onMarkReviewed={() =>
        runQuickAction(
          item.id,
          () => updateItem(item.id, { needs_review: false }),
          'Could not clear review.',
        )
      }
    />
  );

  const listHeader = items.length > 0 ? (
    <View style={styles.listHeader}>
      {gaps ? (
        <View style={styles.gapsCard}>
          <Text style={styles.gapsKicker}>Wardrobe balance</Text>
          <Text style={styles.gapsSummary}>{gaps.summary}</Text>
          <View style={styles.gapsSlots}>
            {['top', 'bottom', 'shoes', 'outerwear'].map((slot) => (
              <View key={slot} style={styles.gapSlot}>
                <Text style={styles.gapSlotValue}>{gaps.by_slot[slot] ?? 0}</Text>
                <Text style={styles.gapSlotLabel}>{slot}</Text>
              </View>
            ))}
          </View>
          {gaps.gaps[0] ? (
            <Text style={styles.gapsHint}>
              {gaps.gaps[0].title}: {gaps.gaps[0].closet_count}/{gaps.gaps[0].target} ·{' '}
              {gaps.gaps[0].reason}
            </Text>
          ) : null}
        </View>
      ) : null}

      {reviewCount > 0 && cleanFilter !== 'review' ? (
        <Pressable style={styles.reviewBanner} onPress={() => setCleanFilter('review')}>
          <Text style={styles.reviewBannerText}>
            {reviewCount} item{reviewCount === 1 ? '' : 's'} need a quick look
          </Text>
          <Text style={styles.reviewBannerAction}>Review →</Text>
        </Pressable>
      ) : null}

      <View style={styles.statsRow}>
        <Pressable
          style={[styles.statPill, cleanFilter === 'all' && styles.statPillActive]}
          onPress={() => setCleanFilter('all')}
        >
          <Text style={[styles.statValue, cleanFilter === 'all' && styles.statValueActive]}>{items.length}</Text>
          <Text style={[styles.statLabel, cleanFilter === 'all' && styles.statLabelActive]}>All</Text>
        </Pressable>
        <Pressable
          style={[styles.statPill, cleanFilter === 'clean' && styles.statPillActive]}
          onPress={() => setCleanFilter('clean')}
        >
          <Text style={[styles.statValue, cleanFilter === 'clean' && styles.statValueActive]}>{cleanCount}</Text>
          <Text style={[styles.statLabel, cleanFilter === 'clean' && styles.statLabelActive]}>Clean</Text>
        </Pressable>
        <Pressable
          style={[styles.statPill, cleanFilter === 'dirty' && styles.statPillActive]}
          onPress={() => setCleanFilter('dirty')}
        >
          <Text style={[styles.statValue, cleanFilter === 'dirty' && styles.statValueActive]}>{dirtyCount}</Text>
          <Text style={[styles.statLabel, cleanFilter === 'dirty' && styles.statLabelActive]}>Hamper</Text>
        </Pressable>
        <Pressable
          style={[styles.statPill, cleanFilter === 'review' && styles.statPillActive]}
          onPress={() => setCleanFilter('review')}
        >
          <Text style={[styles.statValue, cleanFilter === 'review' && styles.statValueActive]}>{reviewCount}</Text>
          <Text style={[styles.statLabel, cleanFilter === 'review' && styles.statLabelActive]}>Review</Text>
        </Pressable>
      </View>

      <TextInput
        style={styles.searchInput}
        value={searchQuery}
        onChangeText={setSearchQuery}
        placeholder="Search name, brand, color…"
        placeholderTextColor={THEME.utility.textMuted}
        clearButtonMode="while-editing"
      />

      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.filterChips}>
        {SORT_OPTIONS.map((option) => {
          const active = sort === option.key;
          return (
            <Pressable
              key={option.key}
              style={[styles.filterChip, active && styles.filterChipActive]}
              onPress={() => setSort(option.key)}
            >
              <Text style={[styles.filterChipText, active && styles.filterChipTextActive]}>{option.label}</Text>
            </Pressable>
          );
        })}
      </ScrollView>

      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.filterChips}>
        {TAXONOMY.capsules.map((capsule) => {
          const active = tagFilter === capsule;
          return (
            <Pressable
              key={capsule}
              style={[styles.filterChip, active && styles.filterChipActive]}
              onPress={() => setTagFilter((prev) => (prev === capsule ? '' : capsule))}
            >
              <Text style={[styles.filterChipText, active && styles.filterChipTextActive]}>{capsule}</Text>
            </Pressable>
          );
        })}
      </ScrollView>

      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.filterChips}>
        {TAXONOMY.categories.map((cat) => {
          const active = categoryFilter === cat;
          return (
            <Pressable
              key={cat}
              style={[styles.filterChip, active && styles.filterChipActive]}
              onPress={() => setCategoryFilter((prev) => (prev === cat ? '' : cat))}
            >
              <Text style={[styles.filterChipText, active && styles.filterChipTextActive]}>{cat}</Text>
            </Pressable>
          );
        })}
      </ScrollView>

      <Pressable style={styles.moreFiltersToggle} onPress={() => setShowMoreFilters((v) => !v)}>
        <Text style={styles.moreFiltersText}>
          {showMoreFilters ? 'Hide filters' : 'More filters'}
          {(colorFilter || brandFilter || seasonFilter || formalityFilter || tagFilter) ? ' · on' : ''}
        </Text>
      </Pressable>

      {needsCutoutCount > 0 ? (
        <Pressable
          style={styles.improvePhotosBtn}
          onPress={handleImprovePhotos}
          disabled={improvingPhotos}
        >
          <Text style={styles.improvePhotosText}>
            {improvingPhotos ? 'Improving photos…' : `Improve ${needsCutoutCount} photos`}
          </Text>
        </Pressable>
      ) : null}

      {showMoreFilters ? (
        <View style={styles.moreFilters}>
          {colorOptions.length ? (
            <>
              <Text style={styles.filterSectionLabel}>Color</Text>
              <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.filterChips}>
                {colorOptions.map((color) => {
                  const active = colorFilter === color;
                  return (
                    <Pressable
                      key={color}
                      style={[styles.filterChip, active && styles.filterChipActive]}
                      onPress={() => setColorFilter((prev) => (prev === color ? '' : color))}
                    >
                      <Text style={[styles.filterChipText, active && styles.filterChipTextActive]}>{color}</Text>
                    </Pressable>
                  );
                })}
              </ScrollView>
            </>
          ) : null}
          {brandOptions.length ? (
            <>
              <Text style={styles.filterSectionLabel}>Brand</Text>
              <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.filterChips}>
                {brandOptions.map((brand) => {
                  const active = brandFilter === brand;
                  return (
                    <Pressable
                      key={brand}
                      style={[styles.filterChip, active && styles.filterChipActive]}
                      onPress={() => setBrandFilter((prev) => (prev === brand ? '' : brand))}
                    >
                      <Text style={[styles.filterChipText, active && styles.filterChipTextActive]}>{brand}</Text>
                    </Pressable>
                  );
                })}
              </ScrollView>
            </>
          ) : null}
          <Text style={styles.filterSectionLabel}>Season</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.filterChips}>
            {TAXONOMY.seasons.map((season) => {
              const active = seasonFilter === season;
              return (
                <Pressable
                  key={season}
                  style={[styles.filterChip, active && styles.filterChipActive]}
                  onPress={() => setSeasonFilter((prev) => (prev === season ? '' : season))}
                >
                  <Text style={[styles.filterChipText, active && styles.filterChipTextActive]}>{season}</Text>
                </Pressable>
              );
            })}
          </ScrollView>
          <Text style={styles.filterSectionLabel}>Formality</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.filterChips}>
            {TAXONOMY.formality.map((level) => {
              const active = formalityFilter === level;
              return (
                <Pressable
                  key={level}
                  style={[styles.filterChip, active && styles.filterChipActive]}
                  onPress={() => setFormalityFilter((prev) => (prev === level ? '' : level))}
                >
                  <Text style={[styles.filterChipText, active && styles.filterChipTextActive]}>{level}</Text>
                </Pressable>
              );
            })}
          </ScrollView>
          {(colorFilter || brandFilter || seasonFilter || formalityFilter || tagFilter) ? (
            <Pressable onPress={clearExtraFilters}>
              <Text style={styles.clearFilters}>Clear extra filters</Text>
            </Pressable>
          ) : null}
        </View>
      ) : null}

      {laundry ? (
        <View style={[styles.laundryBanner, laundry.laundry_due && styles.laundryBannerDue]}>
          <Text style={[styles.laundryText, laundry.laundry_due && styles.laundryTextDue]} numberOfLines={2}>
            {laundry.laundry_due ? '🧺 ' : '✓ '}{laundry.message}
          </Text>
          {laundry.dirty_count > 0 ? (
            <Pressable onPress={handleWashAll} style={styles.laundryActionBtn}>
              <Text style={styles.laundryActionText}>Done</Text>
            </Pressable>
          ) : null}
        </View>
      ) : null}
    </View>
  ) : null;

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.headerRow}>
        <View style={styles.headerText}>
          <Text style={styles.title}>Closet</Text>
          <Text style={styles.subtitle}>
            {items.length
              ? `${filteredItems.length} showing`
              : 'Snap a flat-lay or add items to get started'}
          </Text>
        </View>
        <Pressable style={styles.addFab} onPress={openAddMenu} accessibilityLabel="Add to closet">
          <Text style={styles.addFabText}>+ Add</Text>
        </Pressable>
      </View>

      <FlatList
        data={filteredItems}
        keyExtractor={(item) => item.id.toString()}
        renderItem={renderItem}
        numColumns={2}
        columnWrapperStyle={filteredItems.length ? styles.row : undefined}
        contentContainerStyle={filteredItems.length ? styles.listContent : styles.emptyContainer}
        ListHeaderComponent={listHeader}
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

      <ClosetItemDetailSheet
        visible={Boolean(detailItem)}
        item={detailItem}
        onClose={() => setDetailItem(null)}
        onEdit={(item) => openEdit(item)}
        onWear={async (item) => {
          await wearItem(item.id);
          const refreshed = useClosetStore.getState().items.find((i) => i.id === item.id);
          if (refreshed) setDetailItem(refreshed);
        }}
        onSoilOrWash={async (item) => {
          if (item.is_clean) await soilItem(item.id);
          else await washItem(item.id);
          const refreshed = useClosetStore.getState().items.find((i) => i.id === item.id);
          if (refreshed) setDetailItem(refreshed);
        }}
        onTagsChange={async (item, tags) => {
          await updateItem(item.id, { tags });
          const refreshed = useClosetStore.getState().items.find((i) => i.id === item.id);
          if (refreshed) setDetailItem(refreshed);
        }}
      />

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
            {editingId ? (
              <Button
                title={replacingPhoto ? 'Updating photo…' : 'Replace photo'}
                variant="outline"
                onPress={openReplacePhotoMenu}
                loading={replacingPhoto}
                style={styles.replacePhotoBtn}
              />
            ) : null}
            {source !== 'manual' && !editingId ? (
              <View style={styles.smartConfirmBanner}>
                <Text style={styles.aiNote}>
                  {looksSolid
                    ? 'Looks solid — save as-is, or expand to tweak.'
                    : checkFields.length
                      ? `Check ${checkFields.length} field${checkFields.length === 1 ? '' : 's'} marked ⚠ — everything else was accepted.`
                      : 'AI filled these in — fields marked ⚠ are worth a check.'}
                </Text>
                {acceptedSummary ? <Text style={styles.acceptedSummary}>{acceptedSummary}</Text> : null}
                <Pressable onPress={() => setShowAllFields((v) => !v)}>
                  <Text style={styles.showAllLink}>
                    {showAllFields ? 'Show only what needs a check' : 'Show all details'}
                  </Text>
                </Pressable>
              </View>
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

            {showField('name') ? (
              <Input label={label('Name', 'name')} value={form.name} onChangeText={(v) => setField('name', v)} placeholder="Black crewneck tee" />
            ) : null}
            {showField('category') ? (
              <ChipSelect
                label={label('Category', 'category')}
                options={TAXONOMY.categories}
                selected={form.category}
                onSelect={(v) => selectOne('category', v)}
              />
            ) : null}
            {showField('subcategory') && TAXONOMY.subcategories[form.category]?.length ? (
              <ChipSelect
                label={label('Subcategory', 'subcategory')}
                options={TAXONOMY.subcategories[form.category]}
                selected={form.subcategory}
                onSelect={(v) => selectOne('subcategory', v)}
              />
            ) : null}
            {showField('brand') ? (
              <Input label={label('Brand', 'brand')} value={form.brand} onChangeText={(v) => setField('brand', v)} placeholder="Uniqlo" />
            ) : null}
            {showField('product_name') ? (
              <Input
                label={label('Product name', 'product_name')}
                value={form.productName}
                onChangeText={(v) => setField('productName', v)}
                placeholder="Slim Fit Chino Pants"
              />
            ) : null}
            {receiptMeta.price != null || receiptMeta.sku ? (
              <Text style={styles.receiptHint}>
                {receiptMeta.price != null ? `$${receiptMeta.price.toFixed(2)}` : ''}
                {receiptMeta.price != null && receiptMeta.sku ? ' · ' : ''}
                {receiptMeta.sku ? `SKU ${receiptMeta.sku}` : ''}
              </Text>
            ) : null}
            {showField('color') ? (
              <Input label={label('Color', 'color')} value={form.color} onChangeText={(v) => setField('color', v)} placeholder="black" />
            ) : null}
            {showField('material') ? (
              <Input label={label('Material', 'material')} value={form.material} onChangeText={(v) => setField('material', v)} placeholder="100% cotton" />
            ) : null}
            {showField('size') ? (
              <Input label={label('Size', 'size')} value={form.size} onChangeText={(v) => setField('size', v)} placeholder="M" />
            ) : null}
            {showField('pattern') ? (
              <ChipSelect
                label={label('Pattern', 'pattern')}
                options={TAXONOMY.patterns}
                selected={form.pattern}
                onSelect={(v) => selectOne('pattern', v)}
              />
            ) : null}
            {showField('formality') ? (
              <ChipSelect
                label={label('Formality', 'formality')}
                options={TAXONOMY.formality}
                selected={form.formality}
                onSelect={(v) => selectOne('formality', v)}
              />
            ) : null}
            {showField('occasion') ? (
              <ChipSelect
                label={label('Occasion', 'occasion')}
                hint="Pick all that apply."
                options={TAXONOMY.occasions}
                selected={form.occasion}
                onSelect={(v) => toggleMulti('occasion', v)}
                multiple
              />
            ) : null}
            {showField('weather_tag') ? (
              <ChipSelect
                label={label('Weather', 'weather_tag')}
                hint="Pick all that apply."
                options={TAXONOMY.weather}
                selected={form.weatherTag}
                onSelect={(v) => toggleMulti('weatherTag', v)}
                multiple
              />
            ) : null}
            {showField('seasons') ? (
              <ChipSelect
                label={label('Seasons', 'seasons')}
                hint="Pick all that apply — used to match outfits to the weather."
                options={TAXONOMY.seasons}
                selected={form.seasons}
                onSelect={(v) => toggleMulti('seasons', v)}
                multiple
              />
            ) : null}
            {!smartConfirm || showAllFields ? (
              <ChipSelect
                label="Capsules"
                hint="Soft groups — Travel, Work, Date, and more."
                options={TAXONOMY.capsules}
                selected={form.tags}
                onSelect={(v) => toggleMulti('tags', v)}
                multiple
              />
            ) : null}

            {(!smartConfirm || showAllFields) ? (
              <View style={styles.switchRow}>
                <Text style={styles.switchLabel}>Is clean</Text>
                <Switch value={form.isClean} onValueChange={(v) => setField('isClean', v)} />
              </View>
            ) : null}

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
                    ? queueIndex < queue.length - 1
                      ? looksSolid
                        ? 'Looks good · Next'
                        : 'Save & Next'
                      : looksSolid
                        ? 'Looks good · Finish'
                        : 'Save & Finish'
                    : editingId
                      ? 'Save Changes'
                      : looksSolid
                        ? 'Looks good — Save'
                        : 'Save to Closet'
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
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 22,
    paddingTop: 12,
    paddingBottom: 8,
  },
  headerText: { flex: 1, paddingRight: 12 },
  title: { ...utilityTitle(28), textAlign: 'left' },
  subtitle: { fontSize: 14, color: THEME.utility.textMuted, marginTop: 4 },
  addFab: {
    backgroundColor: THEME.brand.accent,
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 22,
    ...SHADOW.soft,
  },
  addFabText: { color: '#fff', fontSize: 14, fontWeight: '700' },
  listHeader: { paddingBottom: 8 },
  gapsCard: {
    backgroundColor: THEME.brand.mist,
    borderRadius: 18,
    padding: 14,
    marginBottom: 12,
    gap: 8,
    ...SHADOW.soft,
  },
  gapsKicker: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.8,
    textTransform: 'uppercase',
    color: THEME.editorial.accentDark,
  },
  gapsSummary: { fontSize: 14, lineHeight: 20, color: THEME.utility.text, fontWeight: '600' },
  gapsSlots: { flexDirection: 'row', gap: 8 },
  gapSlot: {
    flex: 1,
    backgroundColor: THEME.utility.surface,
    borderRadius: 12,
    paddingVertical: 8,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: THEME.utility.border,
  },
  gapSlotValue: { fontFamily: FONTS.sans, fontSize: 16, fontWeight: '800', color: THEME.utility.text },
  gapSlotLabel: {
    fontSize: 10,
    fontWeight: '600',
    color: THEME.utility.textMuted,
    textTransform: 'uppercase',
    marginTop: 2,
  },
  gapsHint: { fontSize: 12, lineHeight: 17, color: THEME.utility.textMuted },
  statsRow: { flexDirection: 'row', gap: 10, marginBottom: 14 },
  statPill: {
    flex: 1,
    backgroundColor: THEME.utility.surface,
    borderRadius: 14,
    paddingVertical: 10,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: THEME.utility.border,
  },
  statPillActive: { backgroundColor: THEME.brand.accent, borderColor: THEME.brand.accent },
  statValue: { fontFamily: FONTS.sans, fontSize: 18, fontWeight: '800', color: THEME.utility.text },
  statValueActive: { color: '#fff' },
  statLabel: {
    marginTop: 2,
    fontSize: 11,
    fontWeight: '600',
    color: THEME.utility.textMuted,
    textTransform: 'uppercase',
    letterSpacing: 0.6,
  },
  statLabelActive: { color: 'rgba(255,255,255,0.85)' },
  searchInput: {
    borderWidth: 1,
    borderColor: THEME.utility.border,
    borderRadius: 14,
    paddingVertical: 12,
    paddingHorizontal: 16,
    fontSize: 15,
    backgroundColor: THEME.utility.surface,
    color: THEME.utility.text,
    marginBottom: 12,
  },
  filterChips: { gap: 8, paddingBottom: 12 },
  filterChip: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: THEME.utility.surface,
    borderWidth: 1,
    borderColor: THEME.utility.border,
  },
  filterChipActive: { backgroundColor: THEME.brand.accent, borderColor: THEME.brand.accent },
  filterChipText: { fontSize: 13, color: THEME.utility.text, textTransform: 'capitalize' },
  filterChipTextActive: { color: '#fff', fontWeight: '700' },
  moreFiltersToggle: { marginBottom: 10, alignSelf: 'flex-start' },
  moreFiltersText: {
    fontSize: 13,
    fontWeight: '700',
    color: THEME.editorial.accentDark,
  },
  improvePhotosBtn: {
    alignSelf: 'flex-start',
    marginBottom: 12,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 12,
    backgroundColor: THEME.brand.mist,
    borderWidth: 1,
    borderColor: THEME.utility.border,
  },
  improvePhotosText: {
    fontSize: 13,
    fontWeight: '700',
    color: THEME.brand.ink,
  },
  moreFilters: { gap: 4, marginBottom: 8 },
  filterSectionLabel: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.7,
    textTransform: 'uppercase',
    color: THEME.utility.textMuted,
    marginBottom: 4,
  },
  clearFilters: {
    fontSize: 13,
    fontWeight: '600',
    color: THEME.utility.textMuted,
    marginBottom: 8,
  },
  reviewBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 12,
    marginBottom: 12,
    paddingHorizontal: 14,
    paddingVertical: 12,
    borderRadius: 14,
    backgroundColor: '#E7EDF5',
    borderWidth: 1,
    borderColor: '#D3DDE9',
  },
  reviewBannerText: { flex: 1, fontSize: 13, fontWeight: '600', color: THEME.utility.text },
  reviewBannerAction: { fontSize: 13, fontWeight: '800', color: THEME.editorial.accentDark },
  replacePhotoBtn: { marginBottom: 12 },
  emptyBtn: { marginTop: 12, alignSelf: 'stretch' },
  laundryBanner: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    marginBottom: 12, padding: 14, borderRadius: 14,
    backgroundColor: THEME.utility.surfaceMuted,
  },
  laundryBannerDue: { backgroundColor: '#F5EFE2' },
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
  row: { gap: 12, marginBottom: 12 },
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
  overlay: {
    ...StyleSheet.absoluteFillObject, backgroundColor: 'rgba(0,0,0,0.55)',
    alignItems: 'center', justifyContent: 'center', gap: 12,
  },
  overlayText: { color: '#fff', fontSize: 16, fontWeight: '600' },
  modalContainer: { flex: 1, backgroundColor: THEME.utility.background },
  modalContent: { padding: 22, paddingBottom: 40 },
  modalTitle: { ...utilityTitle(24), marginBottom: 16 },
  preview: { width: '100%', height: 220, borderRadius: 16, marginBottom: 12, backgroundColor: THEME.editorial.pill },
  aiNote: { fontSize: 13, color: THEME.utility.textMuted },
  smartConfirmBanner: {
    gap: 8,
    marginBottom: 12,
    padding: 12,
    borderRadius: 14,
    backgroundColor: THEME.utility.surfaceMuted,
  },
  acceptedSummary: { fontSize: 12, lineHeight: 17, color: THEME.utility.text, fontWeight: '600' },
  showAllLink: {
    fontSize: 13,
    fontWeight: '700',
    color: THEME.editorial.accentDark,
  },
  receiptHint: { fontSize: 13, color: THEME.utility.textMuted, marginBottom: 12, marginTop: -4 },
  queueProgress: { fontSize: 13, color: THEME.brand.ink, fontWeight: '700', marginBottom: 12 },
  switchRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: 8, marginBottom: 20 },
  switchLabel: { fontSize: 16, color: THEME.utility.text, fontWeight: '600' },
  modalActions: { flexDirection: 'row', gap: 10, marginBottom: 12 },
  modalAction: { flex: 1 },
});
