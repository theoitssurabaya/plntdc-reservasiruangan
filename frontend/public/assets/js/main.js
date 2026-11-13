(function () {
    "use strict";
    var hideTimer = null;

    function fadeout() {
        var p = document.querySelector(".preloader");
        if (p && !p.classList.contains("preloader-hidden")) {
            p.style.transition = "opacity 0.35s cubic-bezier(0.4, 0, 0.2, 1)";
            p.classList.add("preloader-hidden");
            p.style.opacity = "0";
            if (hideTimer) clearTimeout(hideTimer);
            hideTimer = setTimeout(function() {
                if (p.classList.contains("preloader-hidden")) {
                    p.style.display = "none";
                }
            }, 360);
        }
    }

    function showPreloader(onCoveredCallback, autoHideDelay) {
        var p = document.querySelector(".preloader");
        if (!p) {
            if (typeof onCoveredCallback === "function") onCoveredCallback();
            return;
        }
        if (hideTimer) {
            clearTimeout(hideTimer);
            hideTimer = null;
        }
        // Tampilkan animasi loading secara instan (0ms) SEBELUM halaman baru dirender
        p.style.transition = "none";
        p.style.display = "table";
        p.style.opacity = "1";
        p.classList.remove("preloader-hidden");
        void p.offsetWidth;

        // Pastikan browser telah melukis preloader di layar terlebih dahulu baru ganti halaman/view
        requestAnimationFrame(function() {
            requestAnimationFrame(function() {
                if (typeof onCoveredCallback === "function") {
                    onCoveredCallback();
                }
                if (autoHideDelay !== false) {
                    var delay = typeof autoHideDelay === "number" ? autoHideDelay : 300;
                    setTimeout(fadeout, delay);
                }
            });
        });
    }

    window.addEventListener('load', function() {
        setTimeout(fadeout, 300);
    });
    // Fallback if load is delayed or already fired
    setTimeout(fadeout, 2000);
    window.hidePreloader = fadeout;
    window.showPreloader = showPreloader;
})();