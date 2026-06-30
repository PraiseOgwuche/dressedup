import { Tabs } from 'expo-router';
import { Text } from 'react-native';
import { THEME } from '../../constants/theme';

export default function TabLayout() {
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
        name="profile"
        options={{
          title: 'You',
          tabBarIcon: () => <Text style={{ fontSize: 22 }}>○</Text>,
        }}
      />
    </Tabs>
  );
}
