var on_key_goto = function(keyCode, targetUrl) {
    document.addEventListener('keydown', function(e) {
        if (e.keyCode == keyCode) {
            window.location.href = targetUrl;
        }
    });
}
