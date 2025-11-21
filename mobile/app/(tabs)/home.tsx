import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuthStore } from '../../store/authStore';
import { COLORS } from '../../constants/config';

export default function HomeScreen() {
  const { user } = useAuthStore();

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView>
        <View style={styles.header}>
          <Text style={styles.title}>DressedUp</Text>
        </View>

        <View style={styles.content}>
          <Text style={styles.welcomeText}>
            Welcome, {user?.full_name}!
          </Text>

          <View style={styles.card}>
            <Text style={styles.cardTitle}>Your Digital Closet</Text>
            <Text style={styles.cardText}>
              Start adding items to your closet to get personalized outfit suggestions.
            </Text>
          </View>

          <View style={styles.placeholderBox}>
            <Text style={styles.placeholderEmoji}>📸</Text>
            <Text style={styles.placeholderText}>
              Daily outfit suggestions coming soon!
            </Text>
          </View>
        </View>
      </ScrollView>
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
    color: COLORS.primary,
    textAlign: 'center',
  },
  content: {
    padding: 20,
  },
  welcomeText: {
    fontSize: 22,
    fontWeight: '700',
    marginBottom: 24,
    color: COLORS.text,
  },
  card: {
    backgroundColor: COLORS.backgroundLight,
    padding: 20,
    borderRadius: 16,
    marginBottom: 20,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 8,
    color: COLORS.text,
  },
  cardText: {
    fontSize: 14,
    color: COLORS.textLight,
    lineHeight: 20,
  },
  placeholderBox: {
    alignItems: 'center',
    padding: 40,
    backgroundColor: COLORS.backgroundLight,
    borderRadius: 16,
  },
  placeholderEmoji: {
    fontSize: 64,
    marginBottom: 16,
  },
  placeholderText: {
    fontSize: 16,
    color: COLORS.textLight,
    textAlign: 'center',
  },
});
