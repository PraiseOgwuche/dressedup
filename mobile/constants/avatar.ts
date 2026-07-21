/**
 * 3D outfit avatar (Home turntable).
 * Set AVATAR_3D_ENABLED to false to revert Home to the 2D gallery only.
 */
export const AVATAR_3D_ENABLED = true;

/** Slow spin speed (radians per second). */
export const AVATAR_SPIN_SPEED = 0.32;

/** Canvas height on Home hero. */
export const AVATAR_VIEWPORT_HEIGHT = 380;

/** Legacy Ready Player Me subdomain (public hosts shut down Jan 2026). */
export const RPM_SUBDOMAIN =
  (typeof process !== 'undefined' && process.env?.EXPO_PUBLIC_RPM_SUBDOMAIN) || 'demo';

/** @deprecated Creator URL no longer resolves; do not open in WebView. */
export const rpmCreatorUrl = () =>
  `https://${RPM_SUBDOMAIN}.readyplayer.me/avatar?frameApi&bodyType=fullbody`;

