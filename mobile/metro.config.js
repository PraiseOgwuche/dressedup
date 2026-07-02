const path = require('path');
const { getDefaultConfig } = require('expo/metro-config');

const config = getDefaultConfig(__dirname);

// three.js ships some CommonJS builds
config.resolver.sourceExts.push('cjs');

// Let Metro bundle .glb 3D models as binary assets (require()-able).
config.resolver.assetExts.push('glb', 'gltf');

// three's package.json exposes separate ESM ("import") and CJS ("require")
// builds. Metro's package-exports resolution picks a different file per
// call site (import vs require()), which loads TWO copies of three.js into
// the bundle ("Multiple instances of Three.js being imported"). That breaks
// @react-three/fiber's native polyfills, which patch THREE prototypes on
// only one of the two copies, so patched loaders (TextureLoader, FileLoader,
// LoaderUtils) silently don't apply everywhere. Force every bare `three`
// resolution to the same ESM file so there's exactly one instance; leave
// deep imports like `three/examples/jsm/...` to the default resolver.
const THREE_ESM_ENTRY = path.resolve(__dirname, 'node_modules/three/build/three.module.js');
const defaultResolveRequest = config.resolver.resolveRequest;
config.resolver.resolveRequest = (context, moduleName, platform) => {
  if (moduleName === 'three') {
    return { type: 'sourceFile', filePath: THREE_ESM_ENTRY };
  }
  if (defaultResolveRequest) {
    return defaultResolveRequest(context, moduleName, platform);
  }
  return context.resolveRequest(context, moduleName, platform);
};

module.exports = config;
