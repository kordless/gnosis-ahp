# Chrome Extension Build Order: AHP Bridge

## Project: AI Hypercall Protocol (AHP) Browser Bridge

### Objective
Create a Chrome extension that automatically detects AHP URLs in Claude conversations and provides one-click execution with result injection back into the chat.

**Successful Claude Extensions:**
- ClaudeT: Adds microphone button to Claude AI's text input area
- Claude Data Fetcher: Adds custom button directly to Claude's chat interface for instant information retrieval
- Claude Chat Exporter: Properly processes deeply nested DOM structures with shared state
- Mem0: Injects logic only on known AI assistant domains, reads last few user/assistant messages

**Modern Extension Patterns:**
- Manifest V3: Service workers replace background processes, event-based extensions encouraged
- Content Security Policy: Be sure to filter for malicious web pages, prefer safer APIs that don't run scripts
- Dynamic injection: Use chrome.scripting.executeScript with functions rather than string execution

**Claude Interface Specifics:**
- CSP restrictions: connect-src limitations, artifacts run in isolated domains
- DOM changes frequently - extensions need robust element detection
- Chat input uses `[role="textbox"][aria-label="Write your prompt to Claude"]` pattern

### Core Functionality

#### 1. Smart URL Detection & Extraction
- Use MutationObserver to monitor Claude chat for new messages (like Claude Chat Exporter)
- Target code blocks within message content specifically
- Regex pattern: `https?://ahp\.nuts\.services/[^\s\n\)]+` (broader pattern for both HTTP/HTTPS)
- Visual highlighting with subtle overlay indicators (avoid intrusive design)

#### 2. Non-Intrusive UI Integration
- Follow ClaudeT pattern: add subtle button near detected URLs
- Use floating overlay approach rather than DOM manipulation
- Consistent with Claude's design system: rounded buttons, proper spacing
- Loading states with Claude-style animations and feedback

#### 3. Intelligent Result Handling
- Parse AHP JSON responses with proper error handling
- Format results for readability (syntax highlighting for JSON, success/error states)
- Auto-inject into chat input using proper DOM selectors
- Wrap in markdown code blocks for Claude consumption

#### 4. Robust Session & Auth Management
- Store bearer tokens in chrome.storage.session (not localStorage - following V3 patterns)
- Auto-refresh tokens when expired (detect auth failures)
- Handle authentication flow seamlessly in background
- Support multiple concurrent requests with proper queuing

### Technical Specifications

#### Manifest (V3) - Modern Pattern
```json
{
  "manifest_version": 3,
  "name": "AHP Bridge for Claude",
  "version": "1.0.0",
  "description": "Execute AHP tool calls directly from Claude conversations",
  "permissions": [
    "activeTab",
    "storage",
    "scripting"
  ],
  "host_permissions": [
    "http://ahp.nuts.services/*",
    "https://ahp.nuts.services/*"
  ],
  "content_scripts": [{
    "matches": ["https://claude.ai/*"],
    "js": ["content.js"],
    "css": ["styles.css"],
    "run_at": "document_idle"
  }],
  "background": {
    "service_worker": "background.js"
  },
  "action": {
    "default_popup": "popup/popup.html",
    "default_title": "AHP Bridge"
  }
}
```

#### Modern Content Script Architecture
- **MutationObserver Pattern**: Watch for DOM changes efficiently (like Claude Chat Exporter)
- **Event Delegation**: Use single event listener with delegation for performance
- **Proper Cleanup**: removeEventListener and observer.disconnect() on unload
- **Error Boundaries**: Wrap all operations in try-catch blocks
- **Debounced Operations**: Prevent excessive API calls during rapid typing

#### Key Implementation Patterns from Research

**Claude Interface Integration (ClaudeT/Claude Data Fetcher approach):**
```javascript
// Robust selector strategy with fallbacks
const chatInputSelectors = [
  '[role="textbox"][aria-label*="Claude"]',
  '[aria-label="Write your prompt to Claude"]',
  '.ProseMirror[contenteditable="true"]',
  'div[contenteditable="true"][role="textbox"]'
];

// MutationObserver for dynamic content (Claude Chat Exporter pattern)
const observer = new MutationObserver((mutations) => {
  mutations.forEach(mutation => {
    if (mutation.type === 'childList') {
      mutation.addedNodes.forEach(node => {
        if (node.nodeType === 1) { // Element node
          processNewContent(node);
        }
      });
    }
  });
});
```

**Modern V3 Message Passing:**
```javascript
// Background service worker
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "executeAHP") {
    executeAHPCall(request.url)
      .then(result => sendResponse({success: true, data: result}))
      .catch(error => sendResponse({success: false, error: error.message}));
    return true; // Keep message channel open for async response
  }
});

// Content script
chrome.runtime.sendMessage({
  action: "executeAHP", 
  url: ahpUrl
}, (response) => {
  if (response.success) {
    injectResult(response.data);
  } else {
    showError(response.error);
  }
});
```

### File Structure
```
ahp-bridge-extension/
├── manifest.json
├── content.js          # Main content script
├── styles.css          # UI styling
├── popup.html          # Extension popup (optional)
├── popup.js            # Popup logic (optional)
└── README.md           # Installation instructions
```

### Implementation Priority (Revised)

#### Phase 1: Foundation (Following Modern Patterns)
- Manifest V3 setup with proper service worker
- MutationObserver-based content detection
- Basic AHP URL detection and highlighting
- Simple execute button with loading states

#### Phase 2: Core Integration
- Robust authentication token management
- Error handling and retry logic
- Result formatting and injection
- Claude-compatible styling and animations

#### Phase 3: Production Polish
- Comprehensive error boundaries and logging
- Performance optimization (debouncing, efficient DOM operations)
- Settings panel with token configuration
- Response history and session management

### Modern Security & Performance Considerations

#### Content Security Policy Compliance
- Use `JSON.parse()` instead of `eval()` for response parsing
- Prefer `setTimeout(() => {}, delay)` over string-based execution
- Filter for malicious web page content before processing

#### Chrome Storage API (V3 Pattern)
```javascript
// Session-based token storage (clears on browser restart)
await chrome.storage.session.set({
  'ahp_bearer_token': token,
  'ahp_token_expiry': Date.now() + (30 * 60 * 1000) // 30 min
});

// Persistent settings
await chrome.storage.sync.set({
  'ahp_server_url': 'http://ahp.nuts.services',
  'ahp_auth_token': 'f00bar'
});
```

#### Performance Best Practices
- Use `requestIdleCallback()` for non-critical operations
- Implement proper cleanup in extension lifecycle
- Minimal DOM manipulation - prefer overlay patterns
- Efficient regex patterns for URL detection

### Key Insights from Extension Research

**What Works (from successful Claude extensions):**
- Claude Data Fetcher adds a custom button directly to Claude's chat interface for instant information retrieval
- ClaudeT adds a microphone button to Claude AI's text input area with privacy-focused design with local processing
- Claude Chat Exporter properly processes deeply nested DOM structures with shared state
- Mem0 injects logic only on known AI assistant domains and reads your last few user/assistant messages

**Technical Patterns:**
- Service workers replace background processes in Manifest V3, encouraging event-based extensions
- Be sure to filter for malicious web pages, prefer safer APIs that don't run scripts
- Claude Artifacts can't make API requests to external hosts directly due to CSP restrictions
- Use chrome.scripting.executeScript with functions rather than string execution

**Claude Interface Challenges:**
- Interface changes frequently - extensions need robust element detection
- CSP header restrictions limit connect-src capabilities
- Need to handle dynamic content loading and message streaming

### Success Criteria
1. **Detection**: 100% accuracy in finding AHP URLs in Claude conversations
2. **Execution**: Reliable HTTP request handling with proper error states
3. **Integration**: Smooth workflow that feels native to Claude interface
4. **Performance**: No noticeable impact on Claude chat performance

### Development Notes
- Test with both HTTP and HTTPS variants of AHP server
- Handle CORS preflight requests appropriately
- Ensure extension works with Claude's dynamic content loading
- Consider rate limiting to prevent API abuse
- Add visual feedback for all user interactions

### Deployment
- Package as unpacked extension for development
- Create installation guide for manual loading
- Test across different Chrome versions
- Consider publishing to Chrome Web Store once stable

## Expected Outcome
A Chrome extension that transforms the manual "brain/hand" workflow into an automated bridge, allowing seamless execution of AHP tools directly from Claude conversations with results automatically fed back into the chat context.