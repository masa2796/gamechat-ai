// This file configures the initialization of Sentry on the browser.
// The config you add here will be used whenever a page is visited.
// https://docs.sentry.io/platforms/javascript/guides/nextjs/

import * as Sentry from "@sentry/nextjs";

const isProduction = process.env.NODE_ENV === "production";
const isStaging = process.env.VERCEL_ENV === "preview";

Sentry.init({
  dsn: "https://480d40ae9f36e9fc7b8a66a312255116@o4509535066390528.ingest.us.sentry.io/4509535096406016",

  // 本番環境でのコスト最適化: パフォーマンス監視のサンプリング率を調整
  tracesSampleRate: isProduction ? 0.1 : isStaging ? 0.3 : 1.0,

  // エラーサンプリング率
  sampleRate: isProduction ? 0.9 : 1.0,

  // セッションリプレイのサンプリング率（本番環境ではコスト考慮）
  replaysSessionSampleRate: isProduction ? 0.01 : 0.1,
  replaysOnErrorSampleRate: isProduction ? 0.1 : 1.0,

  // 環境設定
  environment: isProduction ? "production" : isStaging ? "staging" : "development",

  // 本番環境ではデバッグモード無効（developmentビルドでのみ有効）
  debug: false,

  // パフォーマンス監視の詳細設定
  integrations: [
    Sentry.replayIntegration({
      // セッションリプレイの設定
      maskAllText: isProduction, // 本番環境では全テキストをマスク
      blockAllMedia: isProduction, // 本番環境では全メディアをブロック
    }),
    Sentry.browserTracingIntegration({
      // 自動計測の制御
      instrumentNavigation: true,
      instrumentPageLoad: true,
    }),
  ],

  // エラーフィルタリング（ノイズ軽減）
  beforeSend(event, _hint) {
    // 開発環境では全てのエラーを送信
    if (!isProduction) return event;

    // 本番環境でのフィルタリング
    // よくあるブラウザエラーをフィルタリング
    if (
      event.exception?.values?.[0]?.value?.includes("Non-Error promise rejection") ||
      event.exception?.values?.[0]?.value?.includes("ResizeObserver loop limit exceeded") ||
      event.exception?.values?.[0]?.value?.includes("Script error") ||
      event.exception?.values?.[0]?.type === "ChunkLoadError" ||
      event.exception?.values?.[0]?.value?.includes("Loading chunk") ||
      event.exception?.values?.[0]?.value?.includes("Loading CSS chunk")
    ) {
      return null;
    }

    // ネットワークエラーの頻度制限
    if (
      event.exception?.values?.[0]?.type === "TypeError" && 
      event.exception?.values?.[0]?.value?.includes("fetch")
    ) {
      // 15%の確率でネットワークエラーを送信
      return Math.random() < 0.15 ? event : null;
    }

    // 広告ブロッカー関連のエラーをフィルタリング
    if (
      event.exception?.values?.[0]?.value?.includes("google") ||
      event.exception?.values?.[0]?.value?.includes("facebook") ||
      event.exception?.values?.[0]?.value?.includes("analytics")
    ) {
      return null;
    }

    return event;
  },

  // パフォーマンスエントリのフィルタリング
  beforeSendTransaction(event) {
    // 本番環境での不要なトランザクションをフィルタリング
    if (isProduction) {
      // 静的リソースのトランザクションを除外
      if (
        event.transaction?.includes("/_next/") ||
        event.transaction?.includes("/static/") ||
        event.transaction?.includes("/favicon.ico")
      ) {
        return null;
      }
    }
    return event;
  },

  // リリース情報の設定
  release: process.env.VERCEL_GIT_COMMIT_SHA || process.env.npm_package_version,

  // タグ設定
  initialScope: {
    tags: {
      component: "nextjs-client",
      deployment: isProduction ? "production" : "development",
    },
  },
});
