import type { MetadataRoute } from 'next'

export const dynamic = 'force-static'

// ビルド時刻を環境変数から取得（なければビルド時のDateで代用）
const buildTime = process.env.BUILD_TIME ? new Date(process.env.BUILD_TIME) : new Date(2024, 0, 1);

export default function sitemap(): MetadataRoute.Sitemap {
  const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000'

  return [
    {
      url: baseUrl,
      lastModified: buildTime,
      changeFrequency: 'daily',
      priority: 1,
    },
    {
      url: `${baseUrl}/assistant`,
      lastModified: buildTime,
      changeFrequency: 'daily',
      priority: 0.8,
    },
  ]
}
