let keyCodesToUrl = {};

let handle_key = function(e) {
    if (e.keyCode in keyCodesToUrl) {
        window.location.href = keyCodesToUrl[e.keyCode];
    }
}
let on_key_goto = function(keyCode, targetUrl) {
    keyCodesToUrl[keyCode] = targetUrl;
}
let attachQuickKeys = function() {
    document.addEventListener('keydown', handle_key);
}
let removeQuickKeys = function() {
    document.removeEventListener('keydown', handle_key);
}
window.addEventListener('DOMContentLoaded', (event) => {
    attachQuickKeys();
});