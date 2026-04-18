// Shared between main and renderer. The main process uses these values to
// position the native macOS traffic lights; the renderer reads
// TRAFFIC_LIGHT_STRIP_HEIGHT_PX at boot to set the `--titlebar-safe-top` CSS
// variable so sidebar content never overlaps the window controls.

export const TRAFFIC_LIGHT_POSITION = { x: 12, y: 14 } as const

export const TRAFFIC_LIGHT_STRIP_HEIGHT_PX = 28
