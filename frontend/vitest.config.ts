import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: "./vitest.setup.ts",
    include: [
      "src/**/__tests__/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}",
    ],
    coverage: {
      provider: "v8",
      reporter: ["text", "html"],
      reportsDirectory: "./coverage",
      exclude: [
        "**/*.config.{js,ts}",
        "**/out/**",
        "**/public/**",
        "**/*.d.ts",
        "**/node_modules/**",
        "**/src/types/**",
        ".next/**",
        "vendor-chunks/**",
        "tests/e2e/**",
        // テスト不要ファイルを追加
        "src/app/robots.ts",
        "src/app/sitemap.ts",
        "src/app/layout.tsx",
        "src/app/global-error.tsx",
        "src/app/offline/page.tsx",
  // Sentry関連ページ削除済み (MVP)
        "src/app/test/page.tsx",
        "src/components/structured-data.tsx",
  // Sentry関連コンポーネント削除済み (MVP)
        "src/components/pwa-provider.tsx",
        "src/components/global-error-handler.tsx",
        "src/components/ui/breadcrumb.tsx",
        "src/components/ui/separator.tsx",
        "src/components/ui/sheet.tsx",
        "src/components/ui/sidebar.tsx",
        "src/components/ui/tooltip.tsx"
      ]
    },
    reporters: ['default', 'junit'],
    outputFile: {
      junit: './test-results.xml'
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
});