import React, { useState } from 'react';
import {
  Modal,
  View,
  Text,
  StyleSheet,
  Image,
  Pressable,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  Alert,
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';

import { THEME, SHADOW, utilityTitle } from '../constants/theme';
import { OutfitLookBoard } from './OutfitLookBoard';
import { Input } from './ui/Input';
import { Button } from './ui/Button';
import { OutfitSharePayload } from '../types';
import { getApiErrorMessage } from '../services/errors';

type PickedPhoto = { uri: string; name?: string | null; mimeType?: string | null };

interface ShareFitModalProps {
  visible: boolean;
  outfit: OutfitSharePayload | null;
  occasion?: string;
  onClose: () => void;
  onShare: (payload: { caption?: string; photo?: PickedPhoto | null }) => Promise<void>;
}

export function ShareFitModal({ visible, outfit, occasion, onClose, onShare }: ShareFitModalProps) {
  const [caption, setCaption] = useState('');
  const [photo, setPhoto] = useState<PickedPhoto | null>(null);
  const [sharing, setSharing] = useState(false);

  const reset = () => {
    setCaption('');
    setPhoto(null);
    setSharing(false);
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  const pickPhoto = async () => {
    const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permission.granted) return;
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 0.75,
    });
    if (!result.canceled && result.assets[0]) {
      const asset = result.assets[0];
      setPhoto({
        uri: asset.uri,
        name: asset.fileName,
        mimeType: asset.mimeType,
      });
    }
  };

  const handleShare = async () => {
    setSharing(true);
    try {
      await onShare({ caption: caption.trim() || undefined, photo });
      reset();
      onClose();
    } catch (error) {
      Alert.alert('Error', getApiErrorMessage(error, 'Could not share your fit.'));
    } finally {
      setSharing(false);
    }
  };

  if (!outfit) return null;

  const slots = [
    { key: 'top' as const, label: 'Top', item: outfit.top },
    { key: 'bottom' as const, label: 'Bottom', item: outfit.bottom },
    { key: 'shoes' as const, label: 'Shoes', item: outfit.shoes },
    { key: 'outerwear' as const, label: 'Layer', item: outfit.outerwear },
  ];

  return (
    <Modal visible={visible} animationType="slide" transparent onRequestClose={handleClose}>
      <View style={styles.overlay}>
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : undefined}
          style={styles.sheetWrap}
        >
          <View style={styles.sheet}>
            <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
              <Text style={styles.title}>Share to feed</Text>
              <Text style={styles.subtitle}>
                Your outfit board will be attached. Caption and mirror photo are optional.
              </Text>

              <OutfitLookBoard slots={slots} compact />

              {occasion ? (
                <Text style={styles.occasionHint}>Tagged as {occasion}</Text>
              ) : null}

              {photo ? (
                <View style={styles.photoWrap}>
                  <Image source={{ uri: photo.uri }} style={styles.photo} resizeMode="cover" />
                  <Pressable onPress={() => setPhoto(null)} style={styles.removePhoto}>
                    <Text style={styles.removePhotoText}>Remove photo</Text>
                  </Pressable>
                </View>
              ) : (
                <Button title="Add mirror photo" variant="secondary" onPress={pickPhoto} />
              )}

              <Input
                label="Caption (optional)"
                placeholder="Felt good in this today..."
                value={caption}
                onChangeText={setCaption}
              />
            </ScrollView>

            <View style={styles.actions}>
              <Button title="Cancel" variant="secondary" onPress={handleClose} />
              <Button title="Share fit" loading={sharing} onPress={handleShare} />
            </View>
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
  sheetWrap: {
    maxHeight: '92%',
  },
  sheet: {
    backgroundColor: THEME.utility.background,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    paddingTop: 20,
    paddingBottom: 24,
    ...SHADOW.soft,
  },
  content: {
    paddingHorizontal: 22,
    gap: 16,
    paddingBottom: 8,
  },
  title: {
    ...utilityTitle(22),
    textAlign: 'left',
  },
  subtitle: {
    fontSize: 14,
    color: THEME.utility.textMuted,
    lineHeight: 20,
  },
  occasionHint: {
    fontSize: 12,
    fontWeight: '600',
    color: THEME.brand.goldDark,
    textTransform: 'capitalize',
  },
  photoWrap: {
    gap: 8,
  },
  photo: {
    width: '100%',
    height: 220,
    borderRadius: 16,
    backgroundColor: THEME.utility.surfaceMuted,
  },
  removePhoto: {
    alignSelf: 'flex-start',
  },
  removePhotoText: {
    fontSize: 13,
    color: THEME.utility.textMuted,
    fontWeight: '600',
  },
  actions: {
    flexDirection: 'row',
    gap: 10,
    paddingHorizontal: 22,
    paddingTop: 12,
  },
});
