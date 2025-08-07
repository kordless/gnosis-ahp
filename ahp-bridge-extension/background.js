// background.js

console.log("AHP Bridge background script loaded.");

// --- Icon Generation and Action ---
function createIcon() {
    const canvas = new OffscreenCanvas(32, 32);
    const context = canvas.getContext('2d');
    context.fillStyle = '#f0f0f0';
    context.fillRect(0, 0, 32, 32);
    context.font = 'bold 24px sans-serif';
    context.fillStyle = '#333';
    context.textAlign = 'center';
    context.textBaseline = 'middle';
    context.fillText('/A', 16, 16);
    const imageData = context.getImageData(0, 0, 32, 32);
    chrome.action.setIcon({ imageData: imageData });
    console.log("[AHP] Custom icon '/A' has been set.");
}

// Open settings page when the icon is clicked
chrome.action.onClicked.addListener((tab) => {
    chrome.runtime.openOptionsPage();
});

// Run when the extension is installed or updated
chrome.runtime.onInstalled.addListener(() => {
    createIcon();
});


// --- Authentication and Token Management ---

async function getBearerToken() {
    console.log("[AHP] Checking for bearer token...");
    const sessionData = await chrome.storage.session.get(['bearerToken', 'tokenExpiry']);
    if (sessionData.bearerToken && sessionData.tokenExpiry && Date.now() < sessionData.tokenExpiry) {
        console.log(`[AHP] Using cached bearer token. Expires at: ${new Date(sessionData.tokenExpiry).toLocaleTimeString()}`);
        return sessionData.bearerToken;
    }

    console.log("[AHP] No valid bearer token found, fetching a new one.");
    const settingsData = await chrome.storage.sync.get(['ahpSettings']);
    const settings = settingsData.ahpSettings;

    if (!settings || !settings.preSharedKey || !settings.email) {
        console.error("[AHP] Auth settings (email, pre-shared key) are missing.");
        throw new Error("Authentication settings are not configured.");
    }

    const serverUrl = (settings.serverType === 'custom' && settings.customServerUrl)
        ? settings.customServerUrl
        : 'http://ahp.nuts.services';
    
    const authUrl = `${serverUrl}/auth?token=${settings.preSharedKey}&agent_id=${encodeURIComponent(settings.email)}`;
    console.log(`[AHP] Fetching new token from: ${authUrl}`);

    const response = await fetch(authUrl);
    const data = await response.json();

    if (!response.ok || !data.bearer_token) {
        console.error("[AHP] Failed to get bearer token. Response:", data);
        throw new Error(data.error?.message || "Failed to get bearer token.");
    }

    const expiryTime = Date.now() + (55 * 60 * 1000);
    await chrome.storage.session.set({ bearerToken: data.bearer_token, tokenExpiry: expiryTime });
    
    console.log(`[AHP] Successfully fetched and cached a new bearer token. Expires at: ${new Date(expiryTime).toLocaleTimeString()}`);
    return data.bearer_token;
}


// --- Main Message Listener ---

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "executeAHP") {
        console.log(`[AHP] Received 'executeAHP' request for URL: ${request.url}`);

        getBearerToken().then(bearerToken => {
            const urlWithToken = new URL(request.url);
            urlWithToken.searchParams.set('bearer_token', bearerToken);
            
            console.log(`[AHP] Executing fetch for: ${urlWithToken.toString()}`);
            return fetch(urlWithToken.toString());
        })
        .then(response => {
            if (!response.ok) {
                console.error(`[AHP] Network response was not ok: ${response.status} ${response.statusText}`);
            }
            return response.json();
        })
        .then(result => {
            console.log("[AHP] Execution result received:", result);
            if (result.error) {
                throw new Error(result.error.message || JSON.stringify(result.error));
            }
            sendResponse({ success: true, data: result });
        })
        .catch(error => {
            console.error("[AHP] Final execution error:", error);
            sendResponse({ success: false, error: error.message });
        });
        
        return true; // Indicate async response
    }
});
