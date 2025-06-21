// This file configures the initialization of Sentry on the server.
// The config you add here will be used whenever the server handles a request.
// https://docs.sentry.io/platforms/javascript/guides/nextjs/

import * as Sentry from "@sentry/nextjs";

const isProduction = process.env.NODE_ENV === "production";
const isStaging = process.env.VERCEL_ENV === "preview";

Sentry.init({
  dsn: "https://480d40ae9f36e9fc7b8a66a312255116@o4509535066390528.ingest.us.sentry.io/4509535096406016",

  // 本番環境でのコスト最適化: パフォーマンス監視のサンプリング率を調整
  tracesSampleRate: isProduction ? 0.05 : isStaging ? 0.2 : 1.0,

  // エラーサンプリング率（本番環境でのノイズ軽減）
  sampleRate: isProduction ? 0.8 : 1.0,

  // 環境設定
  environment: isProduction ? "production" : isStaging ? "staging" : "development",

  // 本番環境ではデバッグモード無効（developmentビルドでのみ有効）
  debug: false,

  // エラーフィルタリング（ノイズ軽減）
  beforeSend(event, _hint) {
    // 開発環境では全てのエラーを送信
    if (!isProduction) return event;

    // 本番環境でのフィルタリング
    // よくあるサーバーサイドエラーをフィルタリング
    if (
      event.exception?.values?.[0]?.value?.includes("ECONNRESET") ||
      event.exception?.values?.[0]?.value?.includes("ENOTFOUND") ||
      event.exception?.values?.[0]?.value?.includes("timeout") ||
      event.exception?.values?.[0]?.type === "AbortError"
    ) {
      // ネットワーク関連エラーは10%の確率で送信
      return Math.random() < 0.1 ? event : null;
    }

    // 404エラーの頻度制限
    if (event.exception?.values?.[0]?.value?.includes("404")) {
      return Math.random() < 0.05 ? event : null;
    }

    return event;
  },

  // リリース情報の設定
  release: process.env.VERCEL_GIT_COMMIT_SHA || process.env.npm_package_version,

  // タグ設定
  initialScope: {
    tags: {
      component: "nextjs-server",
      deployment: isProduction ? "production" : "development",
    },
  },
});
