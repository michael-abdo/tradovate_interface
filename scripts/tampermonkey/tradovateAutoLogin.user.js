// ==UserScript==
// @name         Tradovate Auto Login
// @namespace    http://tampermonkey.net/
// @version      1.1
// @description  Adds a dropdown for auto login and waits for the "Access Simulation" button to click it automatically.
// @match        https://trader.tradovate.com/welcome*
// @grant        none
// ==/UserScript==

(function() {
    'use strict';

    function login(username, password) {
        const emailInput = document.getElementById("name-input");
        const passwordInput = document.getElementById("password-input");
        if (!emailInput || !passwordInput) {
            console.error("Input fields not found!");
            return;
        }
        const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
        nativeSetter.call(emailInput, username);
        emailInput.dispatchEvent(new Event("input", { bubbles: true }));
        nativeSetter.call(passwordInput, password);
        passwordInput.dispatchEvent(new Event("input", { bubbles: true }));

        setTimeout(() => {
            const loginButton = document.querySelector("button.MuiButton-containedPrimary");
            if (loginButton) {
                loginButton.click();
            } else {
                console.error("Login button not found!");
            }
        }, 500);
    }

    // Credentials will be populated from environment variables by the Python script
    const credentials = {
        "YOUR_USERNAME": "YOUR_PASSWORD"
    };

    function createDropdown() {
        const container = document.createElement("div");
        container.style.position = "fixed";
        container.style.top = "10px";
        container.style.right = "10px";
        container.style.zIndex = 9999;
        container.style.backgroundColor = "white";
        container.style.padding = "5px";
        container.style.border = "1px solid #ccc";
        container.style.borderRadius = "4px";

        const select = document.createElement("select");
        const defaultOption = document.createElement("option");
        defaultOption.textContent = "Select account";
        defaultOption.value = "";
        select.appendChild(defaultOption);

        for (const user in credentials) {
            const option = document.createElement("option");
            option.value = user;
            option.textContent = user;
            select.appendChild(option);
        }

        select.addEventListener("change", function() {
            const selectedUser = this.value;
            if (selectedUser) {
                const selectedPassword = credentials[selectedUser];
                login(selectedUser, selectedPassword);
            }
        });

        container.appendChild(select);
        document.body.appendChild(container);
    }

    function waitForAccessSimulation() {
        const interval = setInterval(() => {
            const buttons = document.querySelectorAll("button.tm");
            for (const btn of buttons) {
                if (btn.textContent.trim() === "Access Simulation") {
                    btn.click();
                    clearInterval(interval);
                    break;
                }
            }
        }, 500);
    }

        createDropdown();
        waitForAccessSimulation();
})();