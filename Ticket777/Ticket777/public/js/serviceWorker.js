var assets = [
    "/",
    "/ticket.html",
    "/buyPage.html",
    "/js/app.js"
]

self.addEventListener("install", function(installEvent){
    installEvent.waitUntil(
        caches.open("my-test-pwa").then(function(cache){
            cache.addAll(assets);
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