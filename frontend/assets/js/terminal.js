// DOM Elements
const terminalInput = document.getElementById('terminal-input');
const chatHistory = document.getElementById('chat-history');

// 🗣️ ARIS Voice Engine (Text-to-Speech)
function speakText(text) {
    // Prevent speaking for system commands or errors
    if ('speechSynthesis' in window && !text.includes("[SYSTEM]")) {
        // Stop any ongoing speech to prevent overlapping
        window.speechSynthesis.cancel();
        
        // Remove code blocks and special characters for smoother speech rendering
        let cleanText = text.replace(/```[\s\S]*?```/g, "Code block displayed on screen.");
        cleanText = cleanText.replace(/[*#_`]/g, "");

        const utterance = new SpeechSynthesisUtterance(cleanText);
        
        // Fetch available voices from the browser
        const voices = window.speechSynthesis.getVoices();
        
        // Try to find a deep male voice
        const maleVoice = voices.find(v => 
            v.name.includes('Male') || 
            v.name.includes('David') || 
            v.name.includes('Mark') || 
            v.name.includes('Daniel')
        );
        
        if (maleVoice) {
            utterance.voice = maleVoice;
        }

        // Voice Settings for a Deep, Smooth, Cinematic AI feel (JARVIS style)
        utterance.pitch = 0.3; 
        utterance.rate = 0.9;  
        utterance.volume = 1.0; 

        window.speechSynthesis.speak(utterance);
    }
}

// Ensure voices are loaded completely
window.speechSynthesis.onvoiceschanged = function() {
    window.speechSynthesis.getVoices();
};

// Typewriter Effect for ARIS and System Responses
async function typeWriter(text, element, isSystem = false) {
    // Safety check for undefined/null text
    if (!text) text = '[No response received]';
    
    // System messages don't get the "ARIS >" prefix
    const prefix = isSystem ? '<span class="text-muted"></span>' : '<span class="text-cyan">ARIS > </span>';
    const msgContainer = document.createElement('div');
    msgContainer.className = 'chat-msg-enter';
    msgContainer.style.marginBottom = "15px";
    msgContainer.style.lineHeight = "1.5";
    msgContainer.innerHTML = prefix;
    element.appendChild(msgContainer);
    
    // Add typing cursor
    const cursor = document.createElement('span');
    cursor.className = 'typing-cursor';
    msgContainer.appendChild(cursor);
    
    chatHistory.scrollTop = chatHistory.scrollHeight;

    for (let i = 0; i < text.length; i++) {
        // Insert character before the cursor
        const charNode = document.createTextNode(text.charAt(i) === '\n' ? '' : text.charAt(i));
        if (text.charAt(i) === '\n') {
            msgContainer.insertBefore(document.createElement('br'), cursor);
        } else {
            msgContainer.insertBefore(charNode, cursor);
        }
        chatHistory.scrollTop = chatHistory.scrollHeight; 
        
        // Play keystroke sound every few characters
        if (i % 4 === 0 && window.VFX) {
            window.VFX.playSound('keystroke', 0.05);
        }
        
        await new Promise(resolve => setTimeout(resolve, 12)); 
    }
    
    // Remove typing cursor after done
    cursor.remove();
}

// ==========================================
// 🎯 RENDER SYSTEM ACTION RESULT
// ==========================================
function renderActionResult(actionName, actionResult) {
    const card = document.createElement('div');
    card.className = 'system-action-card chat-msg-enter';
    
    // Determine icon based on action type
    let icon = '◆';
    let label = 'SYSTEM ACTION';
    
    if (actionName.includes('battery')) { icon = '🔋'; label = 'BATTERY STATUS'; }
    else if (actionName.includes('system_stats')) { icon = '📊'; label = 'SYSTEM STATS'; }
    else if (actionName.includes('network')) { icon = '🌐'; label = 'NETWORK INFO'; }
    else if (actionName.includes('time')) { icon = '🕐'; label = 'SYSTEM TIME'; }
    else if (actionName.includes('screenshot')) { icon = '📸'; label = 'SCREENSHOT'; }
    else if (actionName.includes('open') || actionName.includes('launch')) { icon = '🚀'; label = 'APP LAUNCH'; }
    else if (actionName.includes('youtube') || actionName.includes('play')) { icon = '🎵'; label = 'MEDIA'; }
    else if (actionName.includes('file') || actionName.includes('directory') || actionName.includes('folder')) { icon = '📁'; label = 'FILE SYSTEM'; }
    else if (actionName.includes('volume') || actionName.includes('mute')) { icon = '🔊'; label = 'VOLUME'; }
    else if (actionName.includes('process') || actionName.includes('kill')) { icon = '⚙️'; label = 'PROCESS'; }
    else if (actionName.includes('shutdown') || actionName.includes('restart') || actionName.includes('sleep') || actionName.includes('lock')) { icon = '🖥️'; label = 'SYSTEM CONTROL'; }
    else if (actionName.includes('search') || actionName.includes('google')) { icon = '🔍'; label = 'WEB SEARCH'; }
    else if (actionName.includes('url')) { icon = '🌐'; label = 'WEB NAVIGATE'; }
    
    // Format the result — try to prettify JSON
    let formattedResult = actionResult;
    try {
        const parsed = JSON.parse(actionResult);
        if (typeof parsed === 'object') {
            formattedResult = Object.entries(parsed)
                .filter(([k, v]) => v !== null && v !== undefined)
                .map(([k, v]) => `  ${k.replace(/_/g, ' ').toUpperCase()}: ${v}`)
                .join('\n');
        }
    } catch(e) {
        // Not JSON, use as-is
    }
    
    card.innerHTML = `
        <div class="action-header">${icon} ${label} EXECUTED</div>
        <div class="action-result">${escapeHtmlTerminal(formattedResult)}</div>
    `;
    
    chatHistory.appendChild(card);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

// HTML escape for terminal (preserve line breaks)
function escapeHtmlTerminal(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML.replace(/\n/g, '<br>');
}

// ==========================================
// 🚀 SEND MESSAGE (Session-Aware)
// ==========================================
async function sendMessage(query) {
    if (!query || query.trim() === '') return;
    query = query.trim();
    
    // 1. Display User Message on Screen instantly
    const userMsg = document.createElement('div');
    userMsg.className = 'chat-msg-enter';
    userMsg.style.marginBottom = "15px";
    userMsg.innerHTML = `<span class="text-muted">USER@ARIS:~$ </span><span style="color: var(--text-main);">${query}</span>`;
    chatHistory.appendChild(userMsg);
    chatHistory.scrollTop = chatHistory.scrollHeight;

    try {
        // Add a temporary loading indicator
        const loadingMsg = document.createElement('div');
        loadingMsg.id = "loading-indicator";
        loadingMsg.className = 'chat-msg-enter';
        loadingMsg.innerHTML = `
            <span class="text-cyan">ARIS > </span>
            <span class="text-muted loading-dots">Processing</span>
            <div class="voice-waveform" style="display: inline-flex; margin-left: 8px;">
                <span class="wave-bar" style="background: var(--primary-blue);"></span>
                <span class="wave-bar" style="background: var(--primary-blue);"></span>
                <span class="wave-bar" style="background: var(--primary-blue);"></span>
                <span class="wave-bar" style="background: var(--primary-blue);"></span>
                <span class="wave-bar" style="background: var(--primary-blue);"></span>
            </div>
        `;
        chatHistory.appendChild(loadingMsg);
        chatHistory.scrollTop = chatHistory.scrollHeight;

        // 2. Send the raw input directly to the Python Backend (with session_id)
        const response = await fetch('http://127.0.0.1:8000/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                message: query,
                session_id: window.currentSessionId || null
            })
        });
        
        const data = await response.json();
        
        // Remove the loading indicator
        const loader = document.getElementById("loading-indicator");
        if (loader) loader.remove();
        
        // Handle HTTP errors (422 validation, 500, etc.)
        if (!response.ok) {
            const errDetail = data.detail ? JSON.stringify(data.detail) : `HTTP ${response.status}`;
            const errorMsg = `[SYSTEM ERROR] Backend returned error: ${errDetail}`;
            await typeWriter(errorMsg, chatHistory, true);
            if (window.VFX) window.VFX.screenShake();
            return;
        }

        // 3. Update session_id if a new session was created
        if (data.session_id && data.session_id !== window.currentSessionId) {
            window.currentSessionId = data.session_id;
        }

        // 4. Handle response based on type
        const isSystemMessage = data.type === 'system_command' || data.type === 'history_command' || data.type === 'error';
        
        // Speak only if it's a normal AI chat or system action
        if (data.type === 'chat' || data.type === 'system_action') {
            speakText(data.response);
        }
        
        // Animate text on screen
        await typeWriter(data.response, chatHistory, isSystemMessage);
        
        // 5. Render system action result card if present
        if (data.type === 'system_action' && data.action_result) {
            renderActionResult(data.action_name || 'unknown', data.action_result);
            
            // Success VFX
            if (window.VFX) {
                const rect = chatHistory.getBoundingClientRect();
                window.VFX.createBurst(
                    rect.left + rect.width / 2,
                    rect.bottom - 50,
                    '#10b981',
                    8
                );
                window.VFX.showToast('System action executed successfully.', 'success', 2500);
            }
        }
        
        // Error VFX
        if (data.type === 'error' && window.VFX) {
            window.VFX.screenShake();
            window.VFX.showToast(data.response.substring(0, 80), 'error', 4000);
        }

        // 6. Trigger UI Actions requested by Python
        if (data.action === "reload_tasks" && typeof window.loadTasks === 'function') {
            window.loadTasks();
        }
        
        // 7. Refresh conversation list in sidebar
        if (typeof window.loadConversations === 'function') {
            window.loadConversations();
        }
        
    } catch (error) {
        // Handle API connection errors
        const loader = document.getElementById("loading-indicator");
        if (loader) loader.remove();
        
        const errorMsg = `[SYSTEM ERROR] API Connection Failed: ${error.message}`;
        await typeWriter(errorMsg, chatHistory, true);
        
        // Error VFX
        if (window.VFX) {
            window.VFX.screenShake();
            window.VFX.showToast('Backend connection failed!', 'error', 4000);
        }
    }
}

// 🚀 TERMINAL INPUT: Capture Enter Key
terminalInput.addEventListener('keypress', async function (e) {
    if (e.key === 'Enter' && terminalInput.value.trim() !== '') {
        const query = terminalInput.value.trim();
        terminalInput.value = ''; 
        await sendMessage(query);
    }
});

// Auto-focus on input field when clicking anywhere on the terminal panel
document.querySelector('.terminal-container').addEventListener('click', () => {
    terminalInput.focus();
});

// ==========================================
// 🎤 VOICE CHAT — Speech-to-Text Engine
// ==========================================
let voiceRecognition = null;
let isListening = false;

function initVoiceChat() {
    const voiceBtn = document.getElementById('voice-btn');
    if (!voiceBtn) return;
    
    // Check browser support
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
        voiceBtn.title = 'Voice chat not supported in this browser';
        voiceBtn.classList.add('voice-unsupported');
        voiceBtn.addEventListener('click', () => {
            alert('⚠ Voice chat requires Chrome or Edge browser.');
        });
        return;
    }
    
    // Initialize Speech Recognition
    voiceRecognition = new SpeechRecognition();
    voiceRecognition.continuous = false;       // Stop after one phrase
    voiceRecognition.interimResults = true;    // Show partial results as you speak
    voiceRecognition.lang = 'en-US';
    voiceRecognition.maxAlternatives = 1;
    
    // --- EVENT: Result received ---
    voiceRecognition.onresult = (event) => {
        let finalTranscript = '';
        let interimTranscript = '';
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
                finalTranscript += transcript;
            } else {
                interimTranscript += transcript;
            }
        }
        
        // Show interim results in the input field
        if (interimTranscript) {
            terminalInput.value = interimTranscript;
            terminalInput.placeholder = '🎤 Listening...';
        }
        
        // When speech is finalized, send the message
        if (finalTranscript) {
            terminalInput.value = '';
            terminalInput.placeholder = 'Enter command...';
            stopListening();
            sendMessage(finalTranscript);
        }
    };
    
    // --- EVENT: Recognition ended ---
    voiceRecognition.onend = () => {
        if (isListening) {
            // If still in listening mode, restart (for continuous conversation)
            try {
                voiceRecognition.start();
            } catch(e) {
                stopListening();
            }
        }
    };
    
    // --- EVENT: Error ---
    voiceRecognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        if (event.error === 'no-speech') {
            // Silently restart if no speech detected
            return;
        }
        stopListening();
        
        if (event.error === 'not-allowed') {
            if (window.VFX) {
                window.VFX.showToast('Microphone access denied! Please allow mic access in browser settings.', 'error', 5000);
            } else {
                alert('⚠ Microphone access denied. Please allow microphone access in your browser settings.');
            }
        }
    };
    
    // --- BUTTON CLICK HANDLER ---
    voiceBtn.addEventListener('click', () => {
        if (isListening) {
            stopListening();
        } else {
            startListening();
        }
    });
}

function startListening() {
    if (!voiceRecognition) return;
    
    isListening = true;
    const voiceBtn = document.getElementById('voice-btn');
    voiceBtn.classList.add('recording');
    terminalInput.placeholder = '🎤 Listening... speak now';
    
    // Add visual feedback to the terminal with waveform
    const statusMsg = document.createElement('div');
    statusMsg.id = 'voice-status';
    statusMsg.className = 'voice-active-indicator chat-msg-enter';
    statusMsg.innerHTML = `
        <span class="recording-dot"></span> 
        VOICE INPUT ACTIVE — Speak now...
        <div class="voice-waveform">
            <span class="wave-bar"></span>
            <span class="wave-bar"></span>
            <span class="wave-bar"></span>
            <span class="wave-bar"></span>
            <span class="wave-bar"></span>
            <span class="wave-bar"></span>
            <span class="wave-bar"></span>
        </div>
    `;
    chatHistory.appendChild(statusMsg);
    chatHistory.scrollTop = chatHistory.scrollHeight;
    
    // VFX burst on mic activation
    if (window.VFX) {
        const rect = voiceBtn.getBoundingClientRect();
        window.VFX.createBurst(rect.left + rect.width / 2, rect.top + rect.height / 2, '#ff2d55', 6);
    }
    
    try {
        voiceRecognition.start();
    } catch(e) {
        // Already started
        console.warn('Recognition already running');
    }
}

function stopListening() {
    isListening = false;
    const voiceBtn = document.getElementById('voice-btn');
    if (voiceBtn) voiceBtn.classList.remove('recording');
    terminalInput.placeholder = 'Enter command...';
    
    // Remove voice status indicator
    const status = document.getElementById('voice-status');
    if (status) status.remove();
    
    try {
        voiceRecognition.stop();
    } catch(e) { /* no-op */ }
}

// Initialize voice chat when DOM is ready
document.addEventListener('DOMContentLoaded', initVoiceChat);