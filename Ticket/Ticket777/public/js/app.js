if ("serviceWorker" in navigator) {
    window.addEventListener("load", function() {
        navigator.serviceWorker
            .register("/serviceWorker.js")
            .then(function(reg) {
                console.log("Service Worker registered with scope:", reg.scope);
            })
            .catch(function(err) {
                console.log("Service Worker registration failed", err);
            });
    });
}