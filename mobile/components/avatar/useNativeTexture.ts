import { useEffect, useRef, useState } from 'react';
import { useThree } from '@react-three/fiber/native';
import * as THREE from 'three';

import { loadNativeTexture } from './loadNativeTexture';

/** Loads a remote image as a native texture, disposing the previous one on change/unmount. */
export function useNativeTexture(uri?: string | null): THREE.Texture | null {
  const gl = useThree((state) => state.gl);
  const [texture, setTexture] = useState<THREE.Texture | null>(null);
  const textureRef = useRef<THREE.Texture | null>(null);

  useEffect(() => {
    let alive = true;
    setTexture(null);

    if (!uri) return undefined;

    loadNativeTexture(uri)
      .then((tex) => {
        if (!alive) {
          tex.dispose();
          return;
        }
        textureRef.current?.dispose();
        textureRef.current = tex;
        gl.initTexture(tex);
        setTexture(tex);
      })
      .catch(() => {
        if (alive) setTexture(null);
      });

    return () => {
      alive = false;
      textureRef.current?.dispose();
      textureRef.current = null;
    };
  }, [uri, gl]);

  return texture;
}
