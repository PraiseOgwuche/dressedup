import React, { useMemo } from 'react';
import * as THREE from 'three';

/**
 * Calibrated to the baked head: front surface exists near y≈1.52 and y≈1.59.
 * Eyes sit in the upper face band; mouth lower — mid-head, flush depth.
 */
export function FaceFeatures() {
  const shared = { polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 };

  const eyeWhite = useMemo(
    () => new THREE.MeshStandardMaterial({ color: '#F7F4EF', roughness: 0.45, metalness: 0.02, ...shared }),
    [],
  );
  const iris = useMemo(
    () => new THREE.MeshStandardMaterial({ color: '#2A221C', roughness: 0.5, metalness: 0.04, ...shared }),
    [],
  );
  const brow = useMemo(
    () => new THREE.MeshStandardMaterial({ color: '#3F3228', roughness: 0.9, metalness: 0.01, ...shared }),
    [],
  );
  const lip = useMemo(
    () => new THREE.MeshStandardMaterial({ color: '#A86A62', roughness: 0.58, metalness: 0.02, ...shared }),
    [],
  );
  const nose = useMemo(
    () => new THREE.MeshStandardMaterial({ color: '#B07A5C', roughness: 0.65, metalness: 0.02, ...shared }),
    [],
  );

  // Absolute positions from head mesh samples (not landmark offsets).
  const eyeY = 1.575;
  const browY = 1.592;
  const noseY = 1.555;
  const mouthY = 1.528;
  const faceZ = 0.062;

  return (
    <group>
      {([-1, 1] as const).map((side) => (
        <group key={`eye-${side}`} position={[side * 0.027, eyeY, faceZ]}>
          <mesh material={eyeWhite}>
            <circleGeometry args={[0.01, 16]} />
          </mesh>
          <mesh material={iris} position={[0, 0, 0.001]}>
            <circleGeometry args={[0.005, 12]} />
          </mesh>
        </group>
      ))}

      {([-1, 1] as const).map((side) => (
        <mesh
          key={`brow-${side}`}
          material={brow}
          position={[side * 0.027, browY, faceZ + 0.0005]}
          rotation={[0, 0, side * -0.1]}
          scale={[1.15, 0.32, 1]}
        >
          <circleGeometry args={[0.011, 12]} />
        </mesh>
      ))}

      <mesh material={nose} position={[0, noseY, faceZ + 0.003]} scale={[0.42, 0.85, 0.65]}>
        <sphereGeometry args={[0.009, 10, 8]} />
      </mesh>

      <mesh material={lip} position={[0, mouthY, faceZ + 0.0005]} scale={[1.35, 0.4, 1]}>
        <circleGeometry args={[0.01, 12]} />
      </mesh>
    </group>
  );
}
