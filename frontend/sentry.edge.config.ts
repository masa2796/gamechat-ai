// This file configures the initialization of Sentry for edge features (middleware, edge routes, and so on).
// The config you add here will be used whenever one of the edge features is loaded.
// Note that this config is unrelated to the Vercel Edge Runtime and is also required when running locally.
// https://docs.sentry.io/platforms/javascript/guides/nextjs/

import * as Sentry from "@sentry/nextjs";

const isProduction = process.env.NODE_ENV === "production";
const isStaging = process.env.VERCEL_ENV === "preview";

Sentry.init({
  dsn: "https://480d40ae9f36e9fc7b8a66a312255116@o4509535066390528.ingest.us.sentry.io/4509535096406016",

  // Edge環境では更に厳しいサンプリング率を適用（コスト最適化）
  tracesSampleRate: isProduction ? 0.02 : isStaging ? 0.1 : 1.0,

  // エラーサンプリング率
  sampleRate: isProduction ? 0.5 : 1.0,

  // 環境設定
  environment: isProduction ? "production" : isStaging ? "staging" : "development",

  // 本番環境ではデバッグモード無効（developmentビルドでのみ有効）
  debug: false,

  // Edge環境での軽量化設定
  beforeSend(event, _hint) {
    // 開発環境では全てのエラーを送信
    if (!isProduction) return event;

    // Edge環境でのフィルタリング（ノイズ軽減）
    // ミドルウェア関連の一般的なエラーをフィルタリング
    if (
      event.exception?.values?.[0]?.value?.includes("Failed to fetch") ||
      event.exception?.values?.[0]?.value?.includes("NetworkError") ||
      event.exception?.values?.[0]?.value?.includes("TypeError: fetch failed") ||
      event.exception?.values?.[0]?.type === "AbortError"
    ) {
      // ネットワークエラーは5%の確率で送信
      return Math.random() < 0.05 ? event : null;
    }

    // Edge Runtime特有のエラーをフィルタリング
    if (
      event.exception?.values?.[0]?.value?.includes("Dynamic Code Evaluation") ||
      event.exception?.values?.[0]?.value?.includes("eval is not allowed")
    ) {
      return null;
    }

    return event;
  },

  // リリース情報の設定
  release: process.env.VERCEL_GIT_COMMIT_SHA || process.env.npm_package_version,

  // タグ設定
  initialScope: {
    tags: {
      component: "nextjs-edge",
      deployment: isProduction ? "production" : "development",
    },
  },
});
