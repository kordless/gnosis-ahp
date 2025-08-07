// content.js

console.log("AHP Bridge content script loaded.");

// --- Helper functions for DOM interaction ---
function findChatInput() {
    const selectors = [
        '[role="textbox"][aria-label*="Claude"]',
        '[aria-label="Write your prompt to Claude"]',
        '.ProseMirror[contenteditable="true"]',
        'div[contenteditable="true"][role="textbox"]'
    ];
    for (const selector of selectors) {
        const element = document.querySelector(selector);
        if (element) {
            console.log(`[AHP] Found chat input with selector: ${selector}`);
            return element;
        }
    }
    console.error("[AHP] Could not find Claude chat input box.");
    return null;
}

function findSendButton() {
    const button = document.querySelector('button[aria-label="Send message"]');
    if (button) {
        console.log("[AHP] Found send button.");
    } else {
        console.error("[AHP] Could not find send button.");
    }
    return button;
}

function injectAndSubmit(result) {
    console.log("[AHP] Preparing to inject result into chat box.");
    const chatInput = findChatInput();
    const sendButton = findSendButton();

    if (!chatInput) {
        alert("AHP Bridge: Could not find Claude chat input box to inject result.");
        return;
    }

    const formattedResult = "```json\n" + JSON.stringify(result, null, 2) + "\n```";
    console.log("[AHP] Injecting formatted result:", formattedResult);
    
    chatInput.textContent = formattedResult;
    chatInput.dispatchEvent(new Event('input', { bubbles: true, cancelable: true }));

    setTimeout(() => {
        if (sendButton && !sendButton.disabled) {
            console.log("[AHP] Clicking send button.");
            sendButton.click();
        } else {
            console.error("[AHP] Send button not found or is disabled. Cannot auto-submit.");
            alert("AHP Bridge: Could not automatically send the result. Please press Enter manually.");
        }
    }, 200); // Increased delay slightly for more reliability
}


let ahpUrlRegex;

function updateRegex(serverUrl) {
    const escapedUrl = serverUrl.replace(/[.*+?^${}()|[\\]/g, '\\$&');
    ahpUrlRegex = new RegExp(`${escapedUrl}/[^\\s\\n\\)]+`, 'g');
    console.log(`[AHP] URL detection regex updated for server: ${serverUrl}`);
}

function findAndProcessAhpUrls(contextNode) {
    if (!ahpUrlRegex) return;

    const codeBlocks = contextNode.querySelectorAll('code');
    codeBlocks.forEach(block => {
        if (block.textContent.match(ahpUrlRegex) && !block.dataset.ahpProcessed) {
            console.log("[AHP] Found AHP URL in a code block:", block.textContent);
            block.dataset.ahpProcessed = 'true';
            const newHtml = block.innerHTML.replace(ahpUrlRegex, (url) => {
                return `${url}<button class="ahp-execute-btn" data-url="${url}">⚡ Execute</button>`;
            });
            block.innerHTML = newHtml;
        }
    });
}

// --- Initialize settings and start observing ---
function initialize() {
    console.log("[AHP] Initializing extension settings...");
    chrome.storage.sync.get(['ahpSettings'], (result) => {
        const settings = result.ahpSettings || { serverType: 'default' };
        let serverUrl;

        if (settings.serverType === 'custom' && settings.customServerUrl) {
            serverUrl = settings.customServerUrl;
        } else {
            serverUrl = 'http://ahp.nuts.services';
        }
        console.log("[AHP] Loaded settings. Using server URL:", serverUrl);
        
        updateRegex(serverUrl);
        findAndProcessAhpUrls(document.body);
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    });
}

// Listen for changes to settings
chrome.storage.onChanged.addListener((changes, namespace) => {
    if (namespace === 'sync' && changes.ahpSettings) {
        console.log("[AHP] Settings changed. Re-initializing.");
        observer.disconnect();
        initialize();
    }
});

// --- Event Delegation for Execute Buttons ---
document.body.addEventListener('click', event => {
    if (event.target.classList.contains('ahp-execute-btn')) {
        const url = event.target.dataset.url;
        console.log(`[AHP] Execute button clicked for URL: ${url}`);
        event.target.textContent = 'Executing...';
        event.target.disabled = true;

        chrome.runtime.sendMessage({ action: "executeAHP", url: url }, (response) => {
            console.log("[AHP] Received response from background script:", response);
            if (response.success) {
                injectAndSubmit(response.data);
                event.target.textContent = '✅ Injected';
            } else {
                event.target.textContent = '❌ Failed';
                event.target.disabled = false; 
                alert(`AHP Call Failed: ${response.error}`);
            }
        });
    }
});


// --- MutationObserver to detect new messages ---
const observer = new MutationObserver((mutations) => {
    mutations.forEach(mutation => {
        if (mutation.type === 'childList') {
            mutation.addedNodes.forEach(node => {
                if (node.nodeType === 1) { // Element node
                    findAndProcessAhpUrls(node);
                }
            });
        }
    });
});

// Initialize the extension
initialize();