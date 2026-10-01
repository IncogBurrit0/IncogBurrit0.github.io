var assets = [
    "/",
    "/ticket.html",
    "/buyPage.html",
    "/js/app.js",
    "/manifest.json",
    "/icon-192.svg",
    "/icon-512.svg"
]

self.addEventListener("install", function(installEvent){
    installEvent.waitUntil(
        caches.open("ticket777-cache-v1").then(function(cache){
            return cache.addAll(assets);
        })
    )
})

self.addEventListener("fetch", function(fetchEvent){
    fetchEvent.respondWith(
        caches.match(fetchEvent.request).then(function(res){
            return res || fetch(fetchEvent.request);
        })
    )
})

self.addEventListener('activate', function(event) {
  event.waitUntil(
    caches.keys().then(function(keys) {
      return Promise.all(
        keys.filter(function(key) {
          return key !== 'ticket777-cache-v1';
        }).map(function(key) {
          return caches.delete(key);
        })
      );
    })
  );
});
