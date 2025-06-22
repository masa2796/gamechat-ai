// Service Worker for PWA functionality
const CACHE_NAME = 'gamechat-ai-v1.1.0';
const STATIC_CACHE_URLS = [
  '/',
  '/manifest.json',
  '/icon-192.png',
  '/icon-512.png',
  '/apple-touch-icon.png',
  '/icon.svg',
];

// Runtime cache configuration
const RUNTIME_CACHE = 'gamechat-ai-runtime-v1.1.0';
const OFFLINE_PAGE = '/offline';

// Install event - cache static resources
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('SW: Cache opened');
        return cache.addAll(STATIC_CACHE_URLS);
      })
      .then(() => {
        console.log('SW: Skip waiting');
        return self.skipWaiting();
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME && cacheName !== RUNTIME_CACHE) {
            console.log('SW: Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      console.log('SW: Claiming clients');
      return self.clients.claim();
    })
  );
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
  // Skip non-GET requests
  if (event.request.method !== 'GET') {
    return;
  }

  // Skip requests to external APIs
  if (!event.request.url.startsWith(self.location.origin)) {
    return;
  }

  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        // Return cached version or fetch from network
        return response || fetch(event.request).then((response) => {
          // Don't cache API responses or non-successful responses
          if (
            !response || 
            response.status !== 200 || 
            response.type !== 'basic' ||
            event.request.url.includes('/api/')
          ) {
            return response;
          }

          // Clone the response for caching
          const responseToCache = response.clone();

          // Use runtime cache for dynamic content
          const cacheToUse = event.request.url.includes('/_next/') ? RUNTIME_CACHE : CACHE_NAME;

          caches.open(cacheToUse)
            .then((cache) => {
              cache.put(event.request, responseToCache);
            });

          return response;
        });
      })
      .catch(() => {
        // Enhanced fallback for offline scenarios
        if (event.request.destination === 'document') {
          return caches.match('/') || caches.match(OFFLINE_PAGE);
        }
        
        // Return cached assets if available
        return caches.match(event.request);
      })
  );
});

// Background sync for offline form submissions (if needed)
self.addEventListener('sync', (event) => {
  if (event.tag === 'background-sync') {
    console.log('SW: Background sync triggered');
    // Handle background sync logic here
  }
});

// Push notification handler (if needed in the future)
self.addEventListener('push', (event) => {
  if (event.data) {
    const options = {
      body: event.data.text(),
      icon: '/icon-192.png',
      badge: '/icon-96.png',
      vibrate: [100, 50, 100],
      data: {
        dateOfArrival: Date.now(),
        primaryKey: 1
      }
    };

    event.waitUntil(
      self.registration.showNotification('GameChat AI', options)
    );
  }
});
