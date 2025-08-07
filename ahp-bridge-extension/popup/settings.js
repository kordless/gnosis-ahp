// popup.js

const form = document.getElementById('settings-form');
const statusDiv = document.getElementById('status');

// Inputs
const emailInput = document.getElementById('email');
const preSharedKeyInput = document.getElementById('pre-shared-key');
const serverTypeDefault = document.getElementById('server-default');
const serverTypeCustom = document.getElementById('server-custom');
const customServerUrlInput = document.getElementById('custom-server-url');

// Function to update the UI based on the selected server type
function toggleCustomUrlInput() {
    customServerUrlInput.disabled = !serverTypeCustom.checked;
}

// Load saved settings when the popup opens
document.addEventListener('DOMContentLoaded', () => {
    chrome.storage.sync.get(['ahpSettings'], (result) => {
        const settings = result.ahpSettings || { serverType: 'default', email: '', preSharedKey: '' };
        
        emailInput.value = settings.email || '';
        preSharedKeyInput.value = settings.preSharedKey || '';

        if (settings.serverType === 'custom') {
            serverTypeCustom.checked = true;
            customServerUrlInput.value = settings.customServerUrl || '';
        } else {
            serverTypeDefault.checked = true;
        }
        toggleCustomUrlInput();
    });
});

// Add event listeners for radio buttons
serverTypeDefault.addEventListener('change', toggleCustomUrlInput);
serverTypeCustom.addEventListener('change', toggleCustomUrlInput);

// Save settings when the form is submitted
form.addEventListener('submit', (event) => {
    event.preventDefault();
    
    const serverType = serverTypeCustom.checked ? 'custom' : 'default';
    const customServerUrl = customServerUrlInput.value.trim();
    const email = emailInput.value.trim();
    const preSharedKey = preSharedKeyInput.value.trim();

    if (!email || !preSharedKey) {
        statusDiv.textContent = 'Email and Pre-shared Key are required.';
        statusDiv.style.color = 'red';
        return;
    }

    if (serverType === 'custom' && !customServerUrl) {
        statusDiv.textContent = 'Please enter a custom URL.';
        statusDiv.style.color = 'red';
        return;
    }

    const settings = {
        serverType,
        customServerUrl: serverType === 'custom' ? customServerUrl : '',
        email,
        preSharedKey
    };

    chrome.storage.sync.set({ ahpSettings: settings }, () => {
        statusDiv.textContent = 'Settings saved!';
        statusDiv.style.color = 'green';
        setTimeout(() => {
            statusDiv.textContent = '';
        }, 2000);
    });
});