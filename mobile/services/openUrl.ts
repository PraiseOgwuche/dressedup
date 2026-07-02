import * as WebBrowser from 'expo-web-browser';
import { Linking } from 'react-native';

/**
 * Open an external https URL. Uses in-app browser when available; falls back to Linking.
 * iOS sometimes rejects Linking.openURL even when Safari opens — we swallow that noise.
 */
export async function openExternalUrl(url: string): Promise<void> {
  const trimmed = url?.trim();
  if (!trimmed) return;

  try {
    await WebBrowser.openBrowserAsync(trimmed, {
      presentationStyle: WebBrowser.WebBrowserPresentationStyle.AUTOMATIC,
      dismissButtonStyle: 'close',
    });
    return;
  } catch {
    // Fall through to system handler.
  }

  try {
    await Linking.openURL(trimmed);
  } catch {
    // Benign on iOS when the page still opens in Safari.
  }
}
