let keyCodesToUrl = {};
let ctrlKeyCodesToUrl = {};

let handle_key = function(e) {
    if (e.ctrlKey) {
        if (e.keyCode in ctrlKeyCodesToUrl) {
            window.location.href = ctrlKeyCodesToUrl[e.keyCode];
        }
    }
    else if (e.keyCode in keyCodesToUrl) {
        window.location.href = keyCodesToUrl[e.keyCode];
    }
}
let on_key_goto = function(keyCode, targetUrl) {
    keyCodesToUrl[keyCode] = targetUrl;
}
let on_ctrl_key_goto = function(keyCode, targetUrl) {
    ctrlKeyCodesToUrl[keyCode] = targetUrl;
}
let attachQuickKeys = function() {
    document.body.addEventListener('keydown', handle_key);
}
let removeQuickKeys = function() {
    document.body.removeEventListener('keydown', handle_key);
}
window.addEventListener('DOMContentLoaded', (event) => {
    attachQuickKeys();
});