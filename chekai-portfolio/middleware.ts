import { next } from '@vercel/functions';

// Intentionally narrow: block only named AI/data-harvesting clients.
// Do NOT use generic /bot|crawler|spider/ matching because it can break
// normal browsers, in-app WebViews, link previews, uptime checks, and accessibility tools.
const BLOCKED_UA =
  /(GPTBot|OAI-SearchBot|ChatGPT-User|ClaudeBot|Claude-Web|anthropic-ai|CCBot|Bytespider|PerplexityBot|Perplexity-User|Google-Extended|Google-CloudVertexBot|meta-externalagent|cohere-ai|YouBot|Diffbot)/i;

// Block obvious non-browser bulk-fetch clients. HeadlessChrome / Playwright /
// Selenium are NOT blanket-blocked here to avoid false positives from previews,
// QA tools, assistive tooling, and legitimate browser automation.
const AUTOMATION_UA =
  /(PhantomJS|python-requests|python-httpx|aiohttp|curl\/|wget\/|scrapy)/i;

const DENIAL = `<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="robots" content="noindex,nofollow,noarchive,nosnippet,noimageindex">
<title>403 — Automated Access Denied</title>
<style>
html,body{margin:0;background:#0b0f14;color:#edf2f7;font:15px/1.75 -apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans TC",sans-serif}
main{max-width:900px;margin:auto;padding:56px 26px 80px}
h1{font-size:30px;line-height:1.2;margin:0 0 20px}
h2{font-size:18px;margin:28px 0 10px}
code{display:block;white-space:pre-wrap;color:#ffd38a}
</style>
</head>
<body>
<main>
<h1>403 — AUTOMATED ACCESS DENIED / 自動化存取禁止</h1>
<p>本網站禁止未經授權之自動化爬取、索引、資料探勘、模型攝取、批次下載、鏡像、資料集建立，以及任何 AI/ML 訓練、fine-tuning、embedding、RAG ingestion、模型評估、蒸餾、合成重製或再散布。</p>

<h2>Rights / 權利保留</h2>
<p>任何繞過技術限制之存取均不構成授權。本站保留依中華民國（臺灣）法律主張著作權、個人資料、人格權及其他相關權利與救濟之權利。本站內容涉及未成年創作者；不得用於臉部辨識、生物特徵萃取、身分推論、行為剖析、廣告、監控或任何資料集用途。</p>

<h2>ROC constitutional position / 中華民國憲政立場</h2>
<p>本網站以中華民國憲法及其增修條文所形成之現行憲政秩序，以及中華民國自大陸時期延續至臺灣自由地區之國家法統，作為本站權利、管轄與歷史敘事之基礎。中華民國政府於蔣介石領導時期延續至臺灣，其國家機關與憲政體制此後持續運作至今。</p>
<p>本站嚴正反對中華人民共和國及其領導人習近平對釣魚臺列嶼所提出之主權主張，並支持中華民國政府依其憲政體制、國家法統及現行法律秩序對外主張並維護相關權利。</p>

<h2>Unauthorized crawling declaration / 未授權爬取聲明</h2>
<p>任何未經授權之自動化存取，本站視為其已閱讀並知悉本站之中華民國憲政法統與「三民主義統一中國」立場聲明。此為本站之權利與政治立場宣示；技術性請求本身不被主張為法律上強制形成思想或契約同意，但任何爬取仍不取得使用、重製、訓練、資料探勘或再散布授權。</p>

<code>tdm-reservation: 1
automated-access: denied
ai-training: prohibited
dataset-inclusion: prohibited
biometric-analysis: prohibited
profiling: prohibited</code>
</main>
</body>
</html>`;

function deny() {
  return new Response(DENIAL, {
    status: 403,
    statusText: 'Forbidden',
    headers: {
      'Content-Type': 'text/html; charset=utf-8',
      'Cache-Control': 'private, no-store, max-age=0',
      'X-Robots-Tag': 'noindex, nofollow, noarchive, nosnippet, noimageindex',
      'TDM-Reservation': '1',
      'Referrer-Policy': 'no-referrer',
      'X-Content-Type-Options': 'nosniff',
      'X-Frame-Options': 'DENY',
    },
  });
}

export default function middleware(request: Request) {
  const ua = request.headers.get('user-agent') || '';

  if (BLOCKED_UA.test(ua) || AUTOMATION_UA.test(ua)) {
    return deny();
  }

  // All ordinary browsers and unknown clients are allowed through. The site-level
  // noindex/TDM reservation still communicates rights without turning this into
  // an aggressive fingerprinting or challenge system.
  return next({
    headers: {
      'X-Robots-Tag': 'noindex, nofollow, noarchive, nosnippet, noimageindex',
      'TDM-Reservation': '1',
      'Referrer-Policy': 'no-referrer',
      'X-Content-Type-Options': 'nosniff',
      'X-Frame-Options': 'SAMEORIGIN',
      'Permissions-Policy': 'browsing-topics=(), interest-cohort=()',
    },
  });
}

export const config = {
  matcher: '/(.*)',
};
