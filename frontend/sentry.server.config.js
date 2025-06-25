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
        var _a, _b, _c, _d, _e, _f, _g, _h, _j, _k, _l, _m, _o, _p, _q, _r, _s, _t, _u;
        // 開発環境では全てのエラーを送信
        if (!isProduction)
            return event;
        // 本番環境でのフィルタリング
        // よくあるサーバーサイドエラーをフィルタリング
        if (((_d = (_c = (_b = (_a = event.exception) === null || _a === void 0 ? void 0 : _a.values) === null || _b === void 0 ? void 0 : _b[0]) === null || _c === void 0 ? void 0 : _c.value) === null || _d === void 0 ? void 0 : _d.includes("ECONNRESET")) ||
            ((_h = (_g = (_f = (_e = event.exception) === null || _e === void 0 ? void 0 : _e.values) === null || _f === void 0 ? void 0 : _f[0]) === null || _g === void 0 ? void 0 : _g.value) === null || _h === void 0 ? void 0 : _h.includes("ENOTFOUND")) ||
            ((_m = (_l = (_k = (_j = event.exception) === null || _j === void 0 ? void 0 : _j.values) === null || _k === void 0 ? void 0 : _k[0]) === null || _l === void 0 ? void 0 : _l.value) === null || _m === void 0 ? void 0 : _m.includes("timeout")) ||
            ((_q = (_p = (_o = event.exception) === null || _o === void 0 ? void 0 : _o.values) === null || _p === void 0 ? void 0 : _p[0]) === null || _q === void 0 ? void 0 : _q.type) === "AbortError") {
            // ネットワーク関連エラーは10%の確率で送信
            return Math.random() < 0.1 ? event : null;
        }
        // 404エラーの頻度制限
        if ((_u = (_t = (_s = (_r = event.exception) === null || _r === void 0 ? void 0 : _r.values) === null || _s === void 0 ? void 0 : _s[0]) === null || _t === void 0 ? void 0 : _t.value) === null || _u === void 0 ? void 0 : _u.includes("404")) {
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
