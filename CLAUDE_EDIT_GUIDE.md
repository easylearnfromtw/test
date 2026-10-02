# musicetown · Claude UI Edit Guide

Use `claude-interface.html` as the editable UI snapshot. It is copied from the current production `index.html` build.

Current build: R8.9.7-20261002-IOS-SEAMLESS-VINTAGE

## Do not break these functional contracts

- Keep `remote-audio-map.js` loaded before the main inline app script.
- Keep the iOS/PWA tags and icon links in <head>.
- Keep `#localLibrarySheet`, `#libraryCollectionList`, `#playerSheet`, `#glassTransport`, and `#nativeAudioPlayer` IDs.
- Keep `mtAdvanceInPlace()` / `attachGlobalTransport()` for continuous next-track playback.
- Keep `vintage-mode-topbar`, `#vintageSlider`, and the vintage audio functions.
- Keep the mobile library horizontal collection tabs scrollable on iPhone.
- Preserve safe-area usage with `env(safe-area-inset-*)`.

## Safe UI areas to redesign

- Header / home HUD / theme shelf
- 3D homepage spacing and labels
- Detailed player visual layout
- Vintage-mode top strip visual treatment
- Library cards, tabs, search, and row styling
- Bottom mini player styling
- Typography, spacing, glass materials, borders, shadows, motion

## Current requested behavior

1. iOS-first visual language and touch targets.
2. Mobile playlist/library tabs must not get stuck.
3. Add-to-Home-Screen uses the musicetown logo.
4. When one song ends, continue directly to the next track.
5. Vintage mode is at the top of the detailed player and has real audible effects.
6. Preserve Dubai remote-audio playback.

When changing UI, prefer CSS overrides near the end of the file instead of deleting older compatibility rules unless you have fully verified the regression surface.
