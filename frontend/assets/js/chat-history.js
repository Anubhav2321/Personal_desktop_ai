// ==========================================
// 🗂️ ARIS CHAT HISTORY MANAGER
// Manages conversation sessions in the left panel
// ==========================================

const API_BASE = 'http://127.0.0.1:8000/api';

// Global state — shared with terminal.js
window.currentSessionId = null;

// ==========================================
// 🚀 LOAD ALL CONVERSATIONS INTO SIDEBAR
// ==========================================
window.loadConversations = async function() {
    try {
        const response = await fetch(`${API_BASE}/conversations`);
        const data = await response.json();
        
        const listContainer = document.getElementById('chat-sessions-list');
        if (!listContainer) return;
        
        listContainer.innerHTML = '';
        
        if (data.conversations && data.conversations.length > 0) {
            data.conversations.forEach(convo => {
                const card = document.createElement('div');
                card.className = 'chat-session-card';
                card.dataset.sessionId = convo.session_id;
                
                // Highlight active conversation
                if (convo.session_id === window.currentSessionId) {
                    card.classList.add('active');
                }
                
                // Format timestamp
                const timeAgo = formatTimeAgo(convo.updated_at);
                const msgCount = convo.message_count || 0;
                
                card.innerHTML = `
                    <div class="session-info" onclick="switchToChat('${convo.session_id}')">
                        <div class="session-title">${escapeHtml(convo.title)}</div>
                        <div class="session-meta">
                            <span class="session-time">${timeAgo}</span>
                            <span class="session-count">${msgCount} msg${msgCount !== 1 ? 's' : ''}</span>
                        </div>
                    </div>
                    <button class="session-delete-btn" onclick="event.stopPropagation(); deleteChat('${convo.session_id}')" title="Delete conversation">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="3,6 5,6 21,6"></polyline>
                            <path d="M19,6v14a2,2,0,0,1-2,2H7a2,2,0,0,1-2-2V6M8,6V4a2,2,0,0,1,2-2h4a2,2,0,0,1,2,2V6"></path>
                        </svg>
                    </button>
                `;
                
                listContainer.appendChild(card);
            });
        } else {
            listContainer.innerHTML = '<p class="text-muted" style="text-align:center; padding: 20px 0; font-size: 0.8rem;">No conversations yet.<br>Start chatting below.</p>';
        }
    } catch (error) {
        console.error("Failed to load conversations:", error);
    }
}

// ==========================================
// 🚀 CREATE A NEW CONVERSATION
// ==========================================
window.createNewChat = async function() {
    try {
        const response = await fetch(`${API_BASE}/conversations`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: "New Conversation" })
        });
        const data = await response.json();
        
        if (data.status === 'success') {
            window.currentSessionId = data.session_id;
            
            // Clear the terminal chat display
            const chatHistory = document.getElementById('chat-history');
            if (chatHistory) {
                chatHistory.innerHTML = `
                    <div class="system-msg text-green">
                        > New Conversation Session Initialized.<br>
                        > Session ID: ${data.session_id}<br>
                        > ARIS is ready. Awaiting Command...
                    </div>
                `;
            }
            
            // Focus the input
            const input = document.getElementById('terminal-input');
            if (input) input.focus();
            
            // Play a subtle sound effect if available
            playUiSound('click');
            
            // Refresh the sidebar
            await window.loadConversations();
        }
    } catch (error) {
        console.error("Failed to create new chat:", error);
    }
}

// ==========================================
// 🚀 SWITCH TO AN EXISTING CONVERSATION
// ==========================================
window.switchToChat = async function(sessionId) {
    try {
        // Don't reload if already on this chat
        if (sessionId === window.currentSessionId) return;
        
        const response = await fetch(`${API_BASE}/conversations/${sessionId}`);
        const data = await response.json();
        
        window.currentSessionId = sessionId;
        
        // Clear and rebuild the terminal with this conversation's messages
        const chatHistory = document.getElementById('chat-history');
        if (!chatHistory) return;
        
        chatHistory.innerHTML = `
            <div class="system-msg text-green">
                > Loaded conversation: ${escapeHtml(data.title)}<br>
                > Session ID: ${sessionId}<br>
                > ${data.messages.length} messages recovered from databanks.
            </div>
        `;
        
        // Render each message
        if (data.messages && data.messages.length > 0) {
            data.messages.forEach(msg => {
                const msgDiv = document.createElement('div');
                msgDiv.style.marginBottom = '15px';
                msgDiv.style.lineHeight = '1.5';
                
                if (msg.role === 'USER') {
                    msgDiv.innerHTML = `<span class="text-muted">USER@ARIS:~$ </span><span style="color: var(--text-main);">${escapeHtml(msg.message)}</span>`;
                } else {
                    msgDiv.innerHTML = `<span class="text-cyan">ARIS > </span>${escapeHtml(msg.message)}`;
                }
                
                chatHistory.appendChild(msgDiv);
            });
        }
        
        // Scroll to bottom
        chatHistory.scrollTop = chatHistory.scrollHeight;
        
        // Focus input
        const input = document.getElementById('terminal-input');
        if (input) input.focus();
        
        // Play sound
        playUiSound('click');
        
        // Refresh sidebar to update active highlight
        await window.loadConversations();
        
    } catch (error) {
        console.error("Failed to switch to chat:", error);
    }
}

// ==========================================
// 🚀 DELETE A CONVERSATION
// ==========================================
window.deleteChat = async function(sessionId) {
    // Simple confirmation via custom inline approach
    if (!confirm('⚠ Purge this conversation from databanks?')) return;
    
    try {
        await fetch(`${API_BASE}/conversations/${sessionId}`, {
            method: 'DELETE'
        });
        
        // If we deleted the active chat, reset the terminal
        if (sessionId === window.currentSessionId) {
            window.currentSessionId = null;
            const chatHistory = document.getElementById('chat-history');
            if (chatHistory) {
                chatHistory.innerHTML = `
                    <div class="system-msg text-green">
                        > Conversation purged from databanks.<br>
                        > Start a new conversation or select one from CHAT_LOGS.
                    </div>
                `;
            }
        }
        
        // Refresh sidebar
        await window.loadConversations();
        
    } catch (error) {
        console.error("Failed to delete chat:", error);
    }
}

// ==========================================
// 🛠️ UTILITY FUNCTIONS
// ==========================================
function formatTimeAgo(isoString) {
    if (!isoString) return '';
    const now = new Date();
    const date = new Date(isoString);
    const seconds = Math.floor((now - date) / 1000);
    
    if (seconds < 60) return 'just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
    
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function playUiSound(type) {
    // Try to play UI sounds from the sfx directory (optional)
    try {
        const audio = new Audio(`./assets/sfx/${type}.wav`);
        audio.volume = 0.3;
        audio.play().catch(() => {}); // Silently fail if no sound file
    } catch(e) { /* no-op */ }
}
