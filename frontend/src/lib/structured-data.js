export function generateWebAppStructuredData() {
    return {
        "@context": "https://schema.org",
        "@type": "WebApplication",
        "name": "GameChat AI",
        "description": "ゲーム攻略のためのAIアシスタント",
        "url": process.env.NEXT_PUBLIC_SITE_URL || "https://localhost:3000",
        "applicationCategory": "GameApplication",
        "operatingSystem": "Web",
        "offers": {
            "@type": "Offer",
            "price": "0",
            "priceCurrency": "JPY"
        },
        "creator": {
            "@type": "Organization",
            "name": "GameChat AI Team"
        },
        "inLanguage": "ja-JP",
        "isAccessibleForFree": true,
        "potentialAction": {
            "@type": "UseAction",
            "target": {
                "@type": "EntryPoint",
                "urlTemplate": process.env.NEXT_PUBLIC_SITE_URL || "https://localhost:3000"
            }
        }
    };
}
export function generateBreadcrumbStructuredData(items) {
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": items.map((item, index) => ({
            "@type": "ListItem",
            "position": index + 1,
            "name": item.name,
            "item": item.item
        }))
    };
}
export function generateFAQStructuredData(faqs) {
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": faqs.map(faq => ({
            "@type": "Question",
            "name": faq.question,
            "acceptedAnswer": {
                "@type": "Answer",
                "text": faq.answer
            }
        }))
    };
}
