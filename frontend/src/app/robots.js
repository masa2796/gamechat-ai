export const dynamic = 'force-static';
export default function robots() {
    const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000';
    return {
        rules: {
            userAgent: '*',
            allow: '/',
            disallow: ['/api/', '/admin/', '/_next/', '/sw.js'],
        },
        sitemap: `${baseUrl}/sitemap.xml`,
    };
}
