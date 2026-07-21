import React, { useEffect, useState } from 'react';
import * as THREE from 'three';
import { GLTF, GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';

import { AVATAR_HEIGHT } from './bakedAvatar';

// eslint-disable-next-line @typescript-eslint/no-var-requires
const FileSystem: typeof import('expo-file-system/legacy') = (() => {
  try {
    return require('expo-file-system/legacy');
  } catch {
    return require('expo-file-system');
  }
})();

const glbCache = new Map<string, Promise<string>>();

async function localGlbUri(url: string): Promise<string> {
  const cached = glbCache.get(url);
  if (cached) return cached;

  const promise = (async () => {
    if (url.startsWith('file://')) return url;
    const dir = FileSystem.cacheDirectory ?? FileSystem.documentDirectory;
    if (!dir) throw new Error('No cache directory for avatar download');
    const target = `${dir}rpm-${encodeURIComponent(url).slice(-80)}.glb`;
    const info = await FileSystem.getInfoAsync(target);
    if (!info.exists) {
      const result = await FileSystem.downloadAsync(url, target);
      return result.uri;
    }
    return target;
  })();

  glbCache.set(url, promise);
  return promise;
}

function normalizeAvatar(root: THREE.Object3D) {
  root.updateMatrixWorld(true);
  const box = new THREE.Box3().setFromObject(root);
  const size = new THREE.Vector3();
  box.getSize(size);
  if (size.y <= 0.001) return;

  const scale = AVATAR_HEIGHT / size.y;
  root.scale.setScalar(scale);
  root.updateMatrixWorld(true);

  const fitted = new THREE.Box3().setFromObject(root);
  root.position.y -= fitted.min.y;
  root.position.x -= (fitted.min.x + fitted.max.x) / 2;
  root.position.z -= (fitted.min.z + fitted.max.z) / 2;
}

type Props = { url: string; onFailed?: () => void };

/**
 * Loads a remote avatar GLB and fits it to mannequin height.
 */
export function RpmAvatar({ url, onFailed }: Props) {
  const [scene, setScene] = useState<THREE.Object3D | null>(null);

  useEffect(() => {
    let cancelled = false;
    setScene(null);

    (async () => {
      try {
        const localUri = await localGlbUri(url);
        const loader = new GLTFLoader();
        const gltf = await new Promise<GLTF>((resolve, reject) => {
          loader.load(localUri, resolve, undefined, reject);
        });
        if (cancelled) return;
        const root = gltf.scene.clone(true);
        normalizeAvatar(root);
        setScene(root);
      } catch {
        if (!cancelled) onFailed?.();
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [url, onFailed]);

  if (!scene) return null;
  return <primitive object={scene} />;
}
