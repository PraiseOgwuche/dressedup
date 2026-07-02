import { Asset } from 'expo-asset';
import { Image } from 'react-native';
import * as THREE from 'three';

// expo-file-system split cacheDirectory/copyAsync into a legacy subpath; fall
// back to the root import for older SDKs that don't have it.
// eslint-disable-next-line @typescript-eslint/no-var-requires
const FileSystem: typeof import('expo-file-system/legacy') = (() => {
  try {
    return require('expo-file-system/legacy');
  } catch {
    return require('expo-file-system');
  }
})();

const uriCache = new Map<string, Promise<string>>();

function uuidv4(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

async function resolveLocalUri(url: string): Promise<string> {
  const cached = uriCache.get(url);
  if (cached) return cached;

  const promise = (async () => {
    if (url.startsWith('file://')) return url;

    let uri: string;
    if (url.startsWith('http://') || url.startsWith('https://')) {
      const asset = Asset.fromURI(url);
      await asset.downloadAsync();
      uri = asset.localUri ?? asset.uri;
    } else if (url.startsWith('/')) {
      uri = `file://${url}`;
    } else {
      const asset = Asset.fromURI(url);
      await asset.downloadAsync();
      uri = asset.localUri ?? asset.uri;
    }

    if (!uri) {
      throw new Error(`Could not resolve asset URI for ${url}`);
    }

    // Android release builds sometimes return a path without a scheme.
    if (!uri.includes(':')) {
      const file = `${FileSystem.cacheDirectory}ExponentAsset-${uuidv4()}.jpg`;
      await FileSystem.copyAsync({ from: uri, to: file });
      uri = file;
    }

    if (!uri.startsWith('file://') && uri.startsWith('/')) {
      uri = `file://${uri}`;
    }

    return uri;
  })();

  uriCache.set(url, promise);
  return promise;
}

/** Load a remote/local image as a THREE texture in React Native (no document). */
export async function loadNativeTexture(url: string): Promise<THREE.Texture> {
  const localUri = await resolveLocalUri(url);
  const { width, height } = await new Promise<{ width: number; height: number }>((resolve, reject) => {
    Image.getSize(
      localUri,
      (w, h) => resolve({ width: w, height: h }),
      reject,
    );
  });

  const texture = new THREE.Texture();
  // expo-gl reads localUri from this shape (EXGLImageUtils::loadImage).
  texture.image = {
    data: { localUri },
    width,
    height,
  };
  texture.flipY = true;
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.needsUpdate = true;
  (texture as THREE.Texture & { isDataTexture?: boolean }).isDataTexture = true;
  return texture;
}
