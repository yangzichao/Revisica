// electron-builder `afterPack` hook: ad-hoc sign the packaged macOS app.
//
// Without an Apple Developer ID, electron-builder 25 skips signing entirely
// and the app keeps Electron's linker-only signature, which no longer matches
// the bundle (`codesign --verify` fails with "code has no resources but
// signature indicates they must be present"). macOS rejects a downloaded copy
// of such an app as damaged. An ad-hoc signature (no certificate) makes the
// bundle consistent, so users get the normal "Open Anyway" flow instead.
//
// When a Developer ID is configured, electron-builder signs after this hook
// with `--force`, replacing the ad-hoc signature.
const { execFileSync } = require('node:child_process')
const path = require('node:path')

exports.default = async function adhocSignMacApp(context) {
  if (context.electronPlatformName !== 'darwin') {
    return
  }
  const appPath = path.join(
    context.appOutDir,
    `${context.packager.appInfo.productFilename}.app`
  )
  execFileSync('codesign', ['--force', '--deep', '--sign', '-', appPath], {
    stdio: 'inherit'
  })
  execFileSync(
    'codesign',
    ['--verify', '--deep', '--strict', '--verbose=2', appPath],
    { stdio: 'inherit' }
  )
}
