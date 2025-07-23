/**
 * Service Worker for Health Department Inspection System
 * Handles caching and offline functionality
 */

const CACHE_NAME = 'health-inspection-v1';
const urlsToCache = [
    '/',
    '/static/js/offline-forms.js',
    '/static/css/main.css',
    '/static/d.jpg',
    // Form URLs
    '/inspection_form',
    '/spirit_licence_form', 
    '/residential_form',
    '/burial_form',
    '/swimming_pools_form',
    '/small_hotels_form',
    // Dashboard and common pages
    '/dashboard',
    '/static/favicon.ico'
];

// Install Service Worker
self.addEventListener('install', event => {
    console.log('Service Worker installing...');
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('Opened cache');
                return cache.addAll(urlsToCache);
            })
            .catch(error => {
                console.log('Cache installation failed:', error);
                // Don't fail installation if some resources can't be cached
                return Promise.resolve();
            })
    );
});

// Activate Service Worker
self.addEventListener('activate', event => {
    console.log('Service Worker activating...');
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});

// Fetch event - Network First with Cache Fallback strategy
self.addEventListener('fetch', event => {
    const request = event.request;
    const url = new URL(request.url);
    
    // Skip non-GET requests and external requests
    if (request.method !== 'GET' || !url.origin.includes(self.location.origin)) {
        return;
    }
    
    // Handle form submissions separately (they use POST)
    if (request.method === 'POST') {
        return;
    }
    
    event.respondWith(
        // Try network first
        fetch(request)
            .then(response => {
                // If successful, update cache and return response
                if (response.status === 200) {
                    const responseClone = response.clone();
                    caches.open(CACHE_NAME)
                        .then(cache => {
                            cache.put(request, responseClone);
                        })
                        .catch(error => {
                            console.log('Cache update failed:', error);
                        });
                }
                return response;
            })
            .catch(error => {
                console.log('Network request failed, trying cache:', error);
                // If network fails, try cache
                return caches.match(request)
                    .then(response => {
                        if (response) {
                            return response;
                        }
                        
                        // If not in cache, return offline page for navigation requests
                        if (request.mode === 'navigate') {
                            return caches.match('/')
                                .then(offlineResponse => {
                                    return offlineResponse || new Response(
                                        '<h1>Offline</h1><p>You are currently offline. Please check your connection.</p>',
                                        { 
                                            headers: { 'Content-Type': 'text/html' },
                                            status: 200
                                        }
                                    );
                                });
                        }
                        
                        // For other requests, throw the original error
                        throw error;
                    });
            })
    );
});

// Background Sync for form submissions
self.addEventListener('sync', event => {
    if (event.tag === 'form-submission-sync') {
        console.log('Background sync triggered for form submissions');
        event.waitUntil(syncFormSubmissions());
    }
});

async function syncFormSubmissions() {
    try {
        // Open IndexedDB and get pending submissions
        const db = await openDatabase();
        const transaction = db.transaction(['pendingSubmissions'], 'readwrite');
        const store = transaction.objectStore('pendingSubmissions');
        const submissions = await getAllFromStore(store);
        
        let successCount = 0;
        
        for (const submission of submissions) {
            try {
                const formData = new FormData();
                Object.entries(submission.data).forEach(([key, value]) => {
                    formData.append(key, value);
                });
                
                const response = await fetch(submission.actionUrl, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });
                
                if (response.ok) {
                    await store.delete(submission.id);
                    successCount++;
                    console.log('Successfully synced submission:', submission.id);
                } else {
                    console.log('Failed to sync submission:', submission.id, response.status);
                }
            } catch (error) {
                console.log('Error syncing submission:', submission.id, error);
            }
        }
        
        if (successCount > 0) {
            console.log(`Successfully synced ${successCount} submissions`);
            
            // Notify main thread of successful sync
            const clients = await self.clients.matchAll();
            clients.forEach(client => {
                client.postMessage({
                    type: 'SYNC_COMPLETE',
                    syncedCount: successCount
                });
            });
        }
        
    } catch (error) {
        console.log('Background sync failed:', error);
    }
}

function openDatabase() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('HealthInspectionDB', 1);
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
    });
}

function getAllFromStore(store) {
    return new Promise((resolve, reject) => {
        const request = store.getAll();
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
    });
}

// Listen for messages from main thread
self.addEventListener('message', event => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
    
    if (event.data && event.data.type === 'SYNC_NOW') {
        // Trigger immediate sync
        syncFormSubmissions();
    }
});

// Notification handling (for future use)
self.addEventListener('notificationclick', event => {
    event.notification.close();
    
    event.waitUntil(
        clients.openWindow('/dashboard')
    );
});

// Push notification handling (for future use)
self.addEventListener('push', event => {
    const options = {
        body: 'You have pending form submissions to sync.',
        icon: '/static/favicon.ico',
        badge: '/static/favicon.ico',
        tag: 'form-sync-reminder'
    };
    
    event.waitUntil(
        self.registration.showNotification('Health Inspection System', options)
    );
});
