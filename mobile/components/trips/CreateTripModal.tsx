import React, { useEffect, useState } from 'react';
import {
  Alert,
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { TAXONOMY } from '../../constants/config';
import { THEME, utilityTitle } from '../../constants/theme';
import { tripsAPI } from '../../services/api';
import { getApiErrorMessage } from '../../services/errors';
import { TripPlan } from '../../types';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { ChipSelect } from '../ui/ChipSelect';

type Props = {
  visible: boolean;
  onClose: () => void;
  onSaved: () => void | Promise<void>;
  trip?: TripPlan | null;
};

export function CreateTripModal({ visible, onClose, onSaved, trip = null }: Props) {
  const editing = Boolean(trip);
  const [destination, setDestination] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [days, setDays] = useState('3');
  const [weatherTag, setWeatherTag] = useState('');
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!visible) return;
    if (trip) {
      setDestination(trip.destination ?? '');
      setStartDate(trip.start_date ?? '');
      setEndDate(trip.end_date ?? '');
      setDays(String(trip.days ?? 3));
      setWeatherTag(trip.weather_tag ?? '');
      setNotes(trip.notes ?? '');
    } else {
      setDestination('');
      setStartDate('');
      setEndDate('');
      setDays('3');
      setWeatherTag('');
      setNotes('');
    }
  }, [visible, trip]);

  const handleClose = () => {
    onClose();
  };

  const handleSubmit = async () => {
    if (!destination.trim()) {
      Alert.alert('Add a destination', 'Where are you headed?');
      return;
    }

    const hasDates = startDate.trim() && endDate.trim();
    const parsedDays = Number(days);

    if (!hasDates && (Number.isNaN(parsedDays) || parsedDays < 1)) {
      Alert.alert(
        'Add dates or days',
        'Use start & end dates (YYYY-MM-DD) or enter how many days you are away.',
      );
      return;
    }

    const payload = {
      destination: destination.trim(),
      weather_tag: weatherTag || null,
      notes: notes.trim() || null,
      ...(hasDates
        ? { start_date: startDate.trim(), end_date: endDate.trim() }
        : { days: parsedDays, start_date: null, end_date: null }),
    };

    setSubmitting(true);
    try {
      if (editing && trip) {
        await tripsAPI.updatePlan(trip.id, payload);
      } else {
        await tripsAPI.createPlan({
          destination: payload.destination,
          weather_tag: weatherTag || undefined,
          notes: notes.trim() || undefined,
          ...(hasDates
            ? { start_date: startDate.trim(), end_date: endDate.trim() }
            : { days: parsedDays }),
        });
      }
      await onSaved();
      onClose();
    } catch (error) {
      Alert.alert(
        'Error',
        getApiErrorMessage(error, editing ? 'Could not update that trip.' : 'Could not create that trip.'),
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Modal visible={visible} animationType="slide" onRequestClose={handleClose}>
      <View style={styles.container}>
        <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
          <Pressable onPress={handleClose} style={styles.closeLink}>
            <Text style={styles.closeText}>Cancel</Text>
          </Pressable>
          <Text style={styles.title}>{editing ? 'Edit trip' : 'Plan a trip'}</Text>
          <Text style={styles.subtitle}>
            We build a day-by-day outfit plan from your closet and dedupe your suitcase list.
            Add dates for live weather.
          </Text>

          <Input
            label="Destination"
            value={destination}
            onChangeText={setDestination}
            placeholder="Lisbon, Portugal"
          />
          <Input
            label="Start date"
            value={startDate}
            onChangeText={setStartDate}
            placeholder="2026-08-01"
            autoCapitalize="none"
          />
          <Input
            label="End date"
            value={endDate}
            onChangeText={setEndDate}
            placeholder="2026-08-05"
            autoCapitalize="none"
          />
          <Input
            label="Days (if no dates)"
            value={days}
            onChangeText={setDays}
            keyboardType="number-pad"
            placeholder="3"
          />

          <Text style={styles.sectionLabel}>Fallback weather (optional)</Text>
          <Text style={styles.hint}>Used if we cannot fetch a forecast for your dates.</Text>
          <ChipSelect
            options={TAXONOMY.weather}
            selected={weatherTag}
            onSelect={(value) => setWeatherTag((current) => (current === value ? '' : value))}
          />

          <Input
            label="Notes (optional)"
            value={notes}
            onChangeText={setNotes}
            placeholder="Wedding on day 2, lots of walking…"
            multiline
          />
        </ScrollView>

        <View style={styles.actions}>
          <Button
            title={editing ? 'Save changes' : 'Create trip'}
            loading={submitting}
            onPress={handleSubmit}
          />
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: THEME.utility.background },
  content: { padding: 22, gap: 12, paddingBottom: 24 },
  closeLink: { alignSelf: 'flex-start', marginBottom: 4 },
  closeText: { fontSize: 15, fontWeight: '600', color: THEME.editorial.accentDark },
  title: { ...utilityTitle(26), textAlign: 'left' },
  subtitle: { fontSize: 14, lineHeight: 20, color: THEME.utility.textMuted },
  sectionLabel: {
    marginTop: 8,
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 0.8,
    textTransform: 'uppercase',
    color: THEME.utility.textMuted,
  },
  hint: { fontSize: 13, color: THEME.utility.textMuted, marginBottom: 4 },
  actions: { paddingHorizontal: 22, paddingBottom: 28, paddingTop: 8 },
});
