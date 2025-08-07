// chatgpt_content.js

console.log("AHP Bridge content script for ChatGPT loaded.");

// --- Helper functions for DOM interaction (ChatGPT specific) ---
function findChatInput() {
    return document.getElementById('prompt-textarea');
}

function findSendButton() {
    return document.querySelector('button[data-testid="send-button"]');
}

function injectAndSubmit(result) {
    const chatInput = findChatInput();
    if (!chatInput) {
        alert("AHP Bridge: Could not find ChatGPT chat input box.");
        return;
    }
    const formattedResult = "```json\n" + JSON.stringify(result, null, 2) + "\n```";
    chatInput.value = formattedResult;
    chatInput.dispatchEvent(new Event('input', { bubbles: true, cancelable: true }));
    setTimeout(() => {
        const sendButton = findSendButton();
        if (sendButton && !sendButton.disabled) {
            sendButton.click();
        } else {
            alert("AHP Bridge: Could not automatically send the result.");
        }
    }, 200);
}

let ahpUrlRegex;

function updateRegex(serverUrl) {
    const escapedUrl = serverUrl.replace(/[.*+?^${}()|[\\]/g, '\\$&');
    ahpUrlRegex = new RegExp(`${escapedUrl}/[^\\s\\n\\)]+`, 'g');
}

function findAndProcessAhpUrls(contextNode) {
    if (!ahpUrlRegex) return;
    const codeElements = contextNode.querySelectorAll('code');
    codeElements.forEach(code => {
        if (code.textContent.match(ahpUrlRegex) && !code.dataset.ahpProcessed) {
            code.dataset.ahpProcessed = 'true';
            const url = code.textContent.match(ahpUrlRegex)[0];
            const executeBtn = document.createElement('button');
            executeBtn.textContent = '⚡ Execute';
            executeBtn.className = 'ahp-execute-btn';
            executeBtn.dataset.url = url;
            const preElement = code.closest('pre');
            if (preElement) {
                preElement.insertAdjacentElement('afterend', executeBtn);
            } else {
                code.insertAdjacentElement('afterend', executeBtn);
            }
        }
    });
}

// --- DEBUG MODE ---
function runDiagnostics() {
    console.log("--- AHP BRIDGE DIAGNOSTICS ---");
    console.log("Current AHP Regex:", ahpUrlRegex);
    
    const messageContainers = document.querySelectorAll('div[data-message-author-role="assistant"]');
    console.log(`Found ${messageContainers.length} assistant message containers.`);

    let totalCodeBlocks = 0;
    messageContainers.forEach((container, index) => {
        const codeBlocks = container.querySelectorAll('code');
        if (codeBlocks.length > 0) {
            console.log(`- Message #${index + 1} contains ${codeBlocks.length} code block(s).`);
            codeBlocks.forEach(block => {
                const hasMatch = block.textContent.match(ahpUrlRegex);
                console.log(`  - Code content: "${block.textContent}" | Match found: ${hasMatch ? 'YES' : 'NO'}`);
            });
            totalCodeBlocks += codeBlocks.length;
        }
    });
    console.log(`--- Total code blocks found: ${totalCodeBlocks} ---`);
    alert("Diagnostics have been run. Please open the developer console (F12), copy the log, and provide it to the developer.");
}

// --- Initialize settings and start observing ---
function initialize() {
    chrome.storage.sync.get(['ahpSettings'], (result) => {
        const settings = result.ahpSettings || { serverType: 'default' };
        const serverUrl = (settings.serverType === 'custom' && settings.customServerUrl)
            ? settings.customServerUrl
            : 'http://ahp.nuts.services';
        updateRegex(serverUrl);
        findAndProcessAhpUrls(document.body);
        observer.observe(document.body, { childList: true, subtree: true });
    });

    const chatInput = findChatInput();
    if (chatInput) {
        chatInput.addEventListener('input', (e) => {
            if (e.target.value.trim() === '/debug-ahp') {
                runDiagnostics();
                e.target.value = ''; // Clear the command
            }
        });
    }
}

// --- Event Delegation & Observer ---
document.body.addEventListener('click', event => {
    if (event.target.classList.contains('ahp-execute-btn')) {
        const url = event.target.dataset.url;
        event.target.textContent = 'Executing...';
        event.target.disabled = true;
        chrome.runtime.sendMessage({ action: "executeAHP", url: url }, (response) => {
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

const observer = new MutationObserver((mutations) => {
    mutations.forEach(mutation => {
        mutation.addedNodes.forEach(node => {
            if (node.nodeType === 1) findAndProcessAhpUrls(node);
        });
    });
});

// Delay initialization slightly to ensure the page is fully loaded
setTimeout(initialize, 1000);