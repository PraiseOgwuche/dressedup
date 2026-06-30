import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  Alert,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuthStore } from '../../store/authStore';
import { getApiErrorMessage } from '../../services/errors';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { THEME, editorialTitle } from '../../constants/theme';

export default function LoginScreen() {
  const router = useRouter();
  const { login, isLoading, error, clearError } = useAuthStore();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState<{ email?: string; password?: string }>({});

  const validate = () => {
    const newErrors: { email?: string; password?: string } = {};

    if (!email) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(email)) {
      newErrors.email = 'Email is invalid';
    }

    if (!password) {
      newErrors.password = 'Password is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleLogin = async () => {
    if (!validate()) return;

    clearError();
    try {
      await login({ email, password });
      router.replace('/(tabs)/home');
    } catch (error: any) {
      Alert.alert('Login Failed', getApiErrorMessage(error, 'Please check your credentials and try again.'));
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardView}
      >
        <ScrollView contentContainerStyle={styles.scrollContent}>
          <View style={styles.content}>
            <View style={styles.header}>
              <Text style={styles.logo}>DressedUp</Text>
              <Text style={styles.subtitle}>Your intelligent wardrobe assistant</Text>
            </View>

            <View style={styles.form}>
              <Input
                label="Email"
                placeholder="Enter your email"
                value={email}
                onChangeText={setEmail}
                keyboardType="email-address"
                autoCapitalize="none"
                error={errors.email}
              />

              <Input
                label="Password"
                placeholder="Enter your password"
                value={password}
                onChangeText={setPassword}
                secureTextEntry
                error={errors.password}
              />

              {error && (
                <Text style={styles.errorText}>{error}</Text>
              )}

              <Button
                title="Log In"
                onPress={handleLogin}
                loading={isLoading}
                variant="editorial"
                style={styles.loginButton}
              />

              <Button
                title="Create Account"
                onPress={() => router.push('/(auth)/signup')}
                variant="editorialOutline"
              />
            </View>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: THEME.editorial.background,
  },
  keyboardView: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
  },
  content: {
    flex: 1,
    padding: 24,
    justifyContent: 'center',
  },
  header: {
    alignItems: 'center',
    marginBottom: 48,
  },
  logo: {
    ...editorialTitle(40),
    marginBottom: 10,
  },
  subtitle: {
    marginTop: 18,
    fontSize: 15,
    color: THEME.editorial.textMuted,
    textAlign: 'center',
  },
  form: {
    width: '100%',
  },
  loginButton: {
    marginBottom: 12,
  },
  errorText: {
    color: THEME.shared.error,
    textAlign: 'center',
    marginBottom: 16,
  },
});
