import { connectTest, signer, user_address } from "./chainload.js";

class LoginButton extends HTMLElement {
    constructor() {
        super();
        this.innerHTML = '<button id="connect">Connect</button>';
        this.csrf_token = document.querySelector('input[name="csrf_token"]').value;
    }
    connectedCallback() {
        let button = this.querySelector('button#connect');
        button.addEventListener('click', this.connectFunc.bind(this));
    }
    async connectFunc() {
        await connectTest(); // TODO: change to mainnet when ready

        // request the siwe message from the login endpoint by get request
        const url = '/auth/login/' + user_address;
        const response = await fetch(url);
        const data = await response.json();
        this.signAndSendSiweMessage(data.siwe_message);
    }
    async signAndSendSiweMessage(siweMessage) {
        //this.setLabel('Please sign...');
        const flatSig = await signer.signMessage(siweMessage);
        const siweData = {
            'signature': flatSig,
            'address': user_address
        };
        // this auth endpoint will send a file to us..
        const url = '/auth/login/' + user_address;
        // post the signature to the server
        const response = await fetch(url, {
            method: 'POST',
            body: JSON.stringify(siweData),
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.csrf_token
            }
        });
        const data = await response.json();
        if (data.success) {
            // redirect
            window.location.href = data.redirect;
        } else {
            alert(data.message);
        }
    }
}

window.customElements.define('login-button', LoginButton);

