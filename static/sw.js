const CACHE_NAME = 'supermarket-v1';

self.addEventListener('install', event => {
    self.skipWaiting();
});

self.addEventListener('activate', event => {
    event.waitUntil(clients.claim());
});

self.addEventListener('fetch', event => {
    event.respondWith(
        fetch(event.request).catch(() => {
            return new Response('<h1 style="text-align:center;font-family:Tajawal;padding:50px;">لا يوجد اتصال بالسيرفر</h1>', 
                { headers: { 'Content-Type': 'text/html; charset=utf-8' } });
        })
    );
});
