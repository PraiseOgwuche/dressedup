import React, { useCallback, useState } from 'react';
import { Alert, FlatList, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useFocusEffect } from 'expo-router';

import { COLORS } from '../../constants/config';
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
    backgroundColor: '#fff',
  },
  header: {
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  title: {
    fontSize: 24,
    fontWeight: '800',
    color: COLORS.text,
    textAlign: 'center',
  },
  content: {
    flex: 1,
  },
  list: {
    padding: 20,
    gap: 12,
  },
  emptyList: {
    flexGrow: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  comingSoon: {
    fontSize: 16,
    color: COLORS.textLight,
  },
  card: {
    backgroundColor: COLORS.backgroundLight,
    borderRadius: 14,
    padding: 14,
  },
  category: {
    fontSize: 13,
    fontWeight: '800',
    color: COLORS.primary,
  },
  reason: {
    marginTop: 6,
    fontSize: 14,
    color: COLORS.text,
  },
  priority: {
    marginTop: 8,
    fontSize: 12,
    color: COLORS.textLight,
  },
});
