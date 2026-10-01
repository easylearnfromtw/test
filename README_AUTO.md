# musicetown AUTO v1

GitHub-native deployment for musicetown R8.9.1.

## What is automatic
- The website source lives directly in this repository.
- A push to `main` automatically starts `.github/workflows/musicetown-auto.yml`.
- The workflow installs/verifies the 23 × 50 = 1150-track catalog.
- City Pass QR PNGs are generated during the workflow; no manual PNG upload is required.
- The workflow builds `_site` and deploys GitHub Pages.
- Future website updates can be committed directly through the connected GitHub account; browser drag-and-drop upload is not required.

## Current web architecture
- 23 themes
- VAPOR LONDON
- Theme Classification
- centered musicetown logo + right-side search
- Multi Library + Library Pass
- City Pass
- Bluetooth Connection Ritual / iOS bridge-compatible web events
- Media Session
