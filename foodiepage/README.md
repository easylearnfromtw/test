# Foodie Page｜腹地圖

台灣食物論壇 × 地圖化社群的靜態互動 MVP。

## 目前版本
- Mobile-first / Desktop split-view UI
- 純 SVG 示意地圖，**不使用任何地圖 API**
- 地圖 Pin / 店家卡片互動
- 即時排隊、再訪率、外部獎項標籤示意
- 搜尋、篩選、收藏、今天吃什麼互動
- 論壇與地點綁定的內容架構
- `prefers-reduced-motion` / `prefers-reduced-transparency` 降級

## 地圖策略
本 Prototype 使用自製 SVG schematic map，非精確導航圖。正式版若仍維持「不使用第三方地圖 API」，可改成自託管 vector tiles / PMTiles + MapLibre GL JS，將地圖資料與圖磚放在自己的 CDN / static hosting，不向 Google Maps / Mapbox 等 API 發請求。
