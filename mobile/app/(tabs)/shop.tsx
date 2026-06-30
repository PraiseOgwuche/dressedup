import React, { useCallback, useState } from 'react';
import { Alert, FlatList, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useFocusEffect } from 'expo-router';

import { THEME, SHADOW, utilityTitle } from '../../constants/theme';
import { shopAPI } from '../../services/api';
import { ShopRecommendation } from '../../types';

export default function ShopScreen() {
  const [recommendations, setRecommendations] = useState<ShopRecommendation[]>([]);
  const [loading, setLoading] = useState(false);

  const loadRecommendations = useCallback(async () => {
    setLoading(true);
    try {
      const response = await shopAPI.getRecommendations();
      setRecommendations(response.recommendations);
    } catch {
      Alert.alert('Error', 'Could not load recommendations.');
    } finally {
      setLoading(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      loadRecommendations();
    }, [loadRecommendations]),
  );

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Shop</Text>
      </View>
      <FlatList
        data={recommendations}
        keyExtractor={(item, index) => `${item.category}-${index}`}
        onRefresh={loadRecommendations}
        refreshing={loading}
        contentContainerStyle={recommendations.length ? styles.list : styles.emptyList}
        ListEmptyComponent={<Text style={styles.comingSoon}>No recommendations yet.</Text>}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <Text style={styles.category}>{item.category.toUpperCase()}</Text>
            <Text style={styles.reason}>{item.reason}</Text>
            <Text style={styles.priority}>Priority: {item.priority}</Text>
          </View>
        )}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: THEME.utility.background,
  },
  header: {
    paddingHorizontal: 22,
    paddingTop: 12,
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: THEME.utility.border,
  },
  title: {
    ...utilityTitle(28),
    textAlign: 'left',
  },
  content: {
    flex: 1,
  },
  list: {
    padding: 22,
    gap: 14,
  },
  emptyList: {
    flexGrow: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  comingSoon: {
    fontSize: 16,
    color: THEME.utility.textMuted,
  },
  card: {
    backgroundColor: THEME.utility.surface,
    borderRadius: 16,
    padding: 16,
    ...SHADOW.soft,
  },
  category: {
    fontSize: 13,
    fontWeight: '800',
    color: THEME.brand.ink,
  },
  reason: {
    marginTop: 6,
    fontSize: 14,
    color: THEME.utility.text,
  },
  priority: {
    marginTop: 8,
    fontSize: 12,
    color: THEME.utility.textMuted,
  },
});
