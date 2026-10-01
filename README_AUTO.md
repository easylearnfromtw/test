# musicetown AUTO v1

This is a GitHub-native deployment bootstrap.

- `auto-package/package.part-*.b64` stores the latest complete website package in small text chunks.
- `auto-package/manifest.json` verifies the exact SHA-256.
- `.github/workflows/musicetown-auto.yml` automatically reconstructs the package, installs/verifies music, builds `_site`, and deploys GitHub Pages.
- No browser drag-and-drop upload is required for future releases. ChatGPT can update these GitHub files directly through the connected GitHub account.

Current source: musicetown R8.9.1
Target music catalog: 23 themes × 50 = 1150 tracks.
