import { TRAFFIC_LIGHT_STRIP_HEIGHT_PX } from '../../../shared/window-chrome'

function detectPlatform(): string {
  return window.electron?.process?.platform ?? 'unknown'
}

// Adds `platform-<os>` to <html> and sets `--titlebar-safe-top` so any region
// that could overlap with OS window chrome (currently just the macOS traffic
// lights) can reserve the right amount of space via CSS. Call once at boot,
// before React mounts, so the variable is defined for the first paint.
export function applyPlatformChrome(): void {
  const platform = detectPlatform()
  document.documentElement.classList.add(`platform-${platform}`)

  const safeTop = platform === 'darwin' ? `${TRAFFIC_LIGHT_STRIP_HEIGHT_PX}px` : '0px'
  document.documentElement.style.setProperty('--titlebar-safe-top', safeTop)
}
