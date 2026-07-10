import { useCallback } from 'react';
import { Tabs, useFocusEffect } from 'expo-router';
import { Text } from 'react-native';

import { THEME } from '../../constants/theme';
import { useFeedActivityStore } from '../../store/feedActivityStore';

export default function TabLayout() {
  const unreadCount = useFeedActivityStore((state) => state.unreadCount);
  const refreshActivity = useFeedActivityStore((state) => state.refresh);

  useFocusEffect(
    useCallback(() => {
      refreshActivity();
    }, [refreshActivity]),
  );

  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: THEME.brand.ink,
        tabBarInactiveTintColor: '#9CA3AF',
        tabBarStyle: {
          height: 72,
          paddingBottom: 10,
          paddingTop: 8,
          backgroundColor: THEME.utility.surface,
          borderTopColor: THEME.utility.border,
          borderTopWidth: 1,
        },
        tabBarLabelStyle: {
          fontSize: 11,
          fontWeight: '600',
          letterSpacing: 0.2,
        },
        headerShown: false,
      }}
    >
      <Tabs.Screen
        name="home"
        options={{
          title: 'Today',
          tabBarIcon: () => <Text style={{ fontSize: 22 }}>✦</Text>,
        }}
      />
      <Tabs.Screen
        name="closet"
        options={{
          title: 'Closet',
          tabBarIcon: () => <Text style={{ fontSize: 22 }}>▦</Text>,
        }}
      />
      <Tabs.Screen
        name="feed"
        options={{
          title: 'Feed',
          tabBarIcon: () => <Text style={{ fontSize: 22 }}>◎</Text>,
          tabBarBadge: unreadCount > 0 ? (unreadCount > 9 ? '9+' : unreadCount) : undefined,
          tabBarBadgeStyle: {
            backgroundColor: THEME.editorial.accentDark,
            fontSize: 10,
            minWidth: 16,
          },
        }}
      />
      <Tabs.Screen
        name="shop"
        options={{
          title: 'Shop',
          tabBarIcon: () => <Text style={{ fontSize: 22 }}>◇</Text>,
        }}
      />
      <Tabs.Screen
        name="trips"
        options={{
          title: 'Trips',
          tabBarIcon: () => <Text style={{ fontSize: 22 }}>✈</Text>,
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: 'You',
          tabBarIcon: () => <Text style={{ fontSize: 22 }}>○</Text>,
        }}
      />
    </Tabs>
  );
}
