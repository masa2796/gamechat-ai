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
        var _a, _b, _c, _d, _e, _f, _g, _h, _j, _k, _l, _m, _o, _p, _q, _r, _s, _t, _u, _v, _w, _x, _y, _z, _0, _1, _2, _3, _4, _5, _6, _7, _8, _9, _10, _11, _12, _13, _14, _15, _16, _17;
        // 開発環境では全てのエラーを送信
        if (!isProduction)
            return event;
        // 本番環境でのフィルタリング
        // よくあるブラウザエラーをフィルタリング
        if (((_d = (_c = (_b = (_a = event.exception) === null || _a === void 0 ? void 0 : _a.values) === null || _b === void 0 ? void 0 : _b[0]) === null || _c === void 0 ? void 0 : _c.value) === null || _d === void 0 ? void 0 : _d.includes("Non-Error promise rejection")) ||
            ((_h = (_g = (_f = (_e = event.exception) === null || _e === void 0 ? void 0 : _e.values) === null || _f === void 0 ? void 0 : _f[0]) === null || _g === void 0 ? void 0 : _g.value) === null || _h === void 0 ? void 0 : _h.includes("ResizeObserver loop limit exceeded")) ||
            ((_m = (_l = (_k = (_j = event.exception) === null || _j === void 0 ? void 0 : _j.values) === null || _k === void 0 ? void 0 : _k[0]) === null || _l === void 0 ? void 0 : _l.value) === null || _m === void 0 ? void 0 : _m.includes("Script error")) ||
            ((_q = (_p = (_o = event.exception) === null || _o === void 0 ? void 0 : _o.values) === null || _p === void 0 ? void 0 : _p[0]) === null || _q === void 0 ? void 0 : _q.type) === "ChunkLoadError" ||
            ((_u = (_t = (_s = (_r = event.exception) === null || _r === void 0 ? void 0 : _r.values) === null || _s === void 0 ? void 0 : _s[0]) === null || _t === void 0 ? void 0 : _t.value) === null || _u === void 0 ? void 0 : _u.includes("Loading chunk")) ||
            ((_y = (_x = (_w = (_v = event.exception) === null || _v === void 0 ? void 0 : _v.values) === null || _w === void 0 ? void 0 : _w[0]) === null || _x === void 0 ? void 0 : _x.value) === null || _y === void 0 ? void 0 : _y.includes("Loading CSS chunk"))) {
            return null;
        }
        // ネットワークエラーの頻度制限
        if (((_1 = (_0 = (_z = event.exception) === null || _z === void 0 ? void 0 : _z.values) === null || _0 === void 0 ? void 0 : _0[0]) === null || _1 === void 0 ? void 0 : _1.type) === "TypeError" &&
            ((_5 = (_4 = (_3 = (_2 = event.exception) === null || _2 === void 0 ? void 0 : _2.values) === null || _3 === void 0 ? void 0 : _3[0]) === null || _4 === void 0 ? void 0 : _4.value) === null || _5 === void 0 ? void 0 : _5.includes("fetch"))) {
            // 15%の確率でネットワークエラーを送信
            return Math.random() < 0.15 ? event : null;
        }
        // 広告ブロッカー関連のエラーをフィルタリング
        if (((_9 = (_8 = (_7 = (_6 = event.exception) === null || _6 === void 0 ? void 0 : _6.values) === null || _7 === void 0 ? void 0 : _7[0]) === null || _8 === void 0 ? void 0 : _8.value) === null || _9 === void 0 ? void 0 : _9.includes("google")) ||
            ((_13 = (_12 = (_11 = (_10 = event.exception) === null || _10 === void 0 ? void 0 : _10.values) === null || _11 === void 0 ? void 0 : _11[0]) === null || _12 === void 0 ? void 0 : _12.value) === null || _13 === void 0 ? void 0 : _13.includes("facebook")) ||
            ((_17 = (_16 = (_15 = (_14 = event.exception) === null || _14 === void 0 ? void 0 : _14.values) === null || _15 === void 0 ? void 0 : _15[0]) === null || _16 === void 0 ? void 0 : _16.value) === null || _17 === void 0 ? void 0 : _17.includes("analytics"))) {
            return null;
        }
        return event;
    },
    // パフォーマンスエントリのフィルタリング
    beforeSendTransaction(event) {
        var _a, _b, _c;
        // 本番環境での不要なトランザクションをフィルタリング
        if (isProduction) {
            // 静的リソースのトランザクションを除外
            if (((_a = event.transaction) === null || _a === void 0 ? void 0 : _a.includes("/_next/")) ||
                ((_b = event.transaction) === null || _b === void 0 ? void 0 : _b.includes("/static/")) ||
                ((_c = event.transaction) === null || _c === void 0 ? void 0 : _c.includes("/favicon.ico"))) {
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
