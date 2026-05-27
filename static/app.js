/**
 * Phone Log Assistant - Client-side JavaScript
 * Handles speech recognition, API communication, and UI updates
 */

// ─── DOM Elements ─────────────────────────────────────────────────────────────

const chatMessages = document.getElementById('chatMessages');
const textInput = document.getElementById('textInput');
const sendBtn = document.getElementById('sendBtn');
const micBtn = document.getElementById('micBtn');
const voiceStatus = document.getElementById('voiceStatus');

const reasoningText = document.getElementById('reasoningText');
const actionText = document.getElementById('actionText');
const dataPreview = document.getElementById('dataPreview');

const assistantName = document.getElementById('assistantName');
const assistantRole = document.getElementById('assistantRole');

const settingsBtn = document.getElementById('settingsBtn');
const settingsModal = document.getElementById('settingsModal');
const closeSettingsBtn = document.getElementById('closeSettingsBtn');
const identityForm = document.getElementById('identityForm');

const addCallBtn = document.getElementById('addCallBtn');
const addCallModal = document.getElementById('addCallModal');
const closeAddCallBtn = document.getElementById('closeAddCallBtn');
const addCallForm = document.getElementById('addCallForm');

const callsList = document.getElementById('callsList');

// ─── Speech Recognition Setup ─────────────────────────────────────────────────

let recognition = null;
let isListening = false;

if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
        isListening = true;
        micBtn.classList.add('listening');
        voiceStatus.textContent = '🎤 Listening... Speak now';
        voiceStatus.classList.add('active');
    };

    recognition.onresult = (event) => {
        let interimTranscript = '';
        let finalTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
                finalTranscript += transcript;
            } else {
                interimTranscript += transcript;
            }
        }

        if (interimTranscript) {
            textInput.value = interimTranscript;
        }

        if (finalTranscript) {
            textInput.value = finalTranscript;
            sendMessage(finalTranscript);
        }
    };

    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        voiceStatus.textContent = `❌ Error: ${event.error}`;
        stopListening();
    };

    recognition.onend = () => {
        stopListening();
    };
} else {
    micBtn.style.display = 'none';
    voiceStatus.textContent = 'Speech recognition not supported in this browser';
}

function startListening() {
    if (recognition && !isListening) {
        try {
            recognition.start();
        } catch (e) {
            console.error('Failed to start recognition:', e);
        }
    }
}

function stopListening() {
    isListening = false;
    micBtn.classList.remove('listening');
    voiceStatus.textContent = '';
    voiceStatus.classList.remove('active');
}

// ─── Speech Synthesis (Text-to-Speech) ────────────────────────────────────────

function speak(text) {
    if ('speechSynthesis' in window) {
        // Cancel any ongoing speech
        window.speechSynthesis.cancel();
        
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        
        // Try to use a female voice if available
        const voices = window.speechSynthesis.getVoices();
        const femaleVoice = voices.find(v => 
            v.name.toLowerCase().includes('female') || 
            v.name.toLowerCase().includes('samantha') ||
            v.name.toLowerCase().includes('victoria')
        );
        if (femaleVoice) {
            utterance.voice = femaleVoice;
        }
        
        window.speechSynthesis.speak(utterance);
    }
}

// ─── Chat Functions ───────────────────────────────────────────────────────────

function addMessage(text, isUser = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user' : 'assistant'}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = '';  // Start empty, build safely
    
    // Parse and append formatted content safely
    const parts = parseMessageParts(text);
    parts.forEach(part => {
        if (part.type === 'text') {
            contentDiv.appendChild(document.createTextNode(part.content));
        } else if (part.type === 'strong') {
            const strong = document.createElement('strong');
            strong.textContent = part.content;
            contentDiv.appendChild(strong);
        } else if (part.type === 'code') {
            const code = document.createElement('code');
            code.textContent = part.content;
            contentDiv.appendChild(code);
        } else if (part.type === 'br') {
            contentDiv.appendChild(document.createElement('br'));
        }
    });
    
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function parseMessageParts(text) {
    // Parse markdown-like syntax into safe parts
    const parts = [];
    let remaining = text;
    
    while (remaining.length > 0) {
        // Check for **bold**
        const boldMatch = remaining.match(/^\*\*(.+?)\*\*/);
        if (boldMatch) {
            parts.push({ type: 'strong', content: boldMatch[1] });
            remaining = remaining.slice(boldMatch[0].length);
            continue;
        }
        
        // Check for `code`
        const codeMatch = remaining.match(/^`(.+?)`/);
        if (codeMatch) {
            parts.push({ type: 'code', content: codeMatch[1] });
            remaining = remaining.slice(codeMatch[0].length);
            continue;
        }
        
        // Check for newline
        if (remaining.startsWith('\n')) {
            parts.push({ type: 'br' });
            remaining = remaining.slice(1);
            continue;
        }
        
        // Find next special character
        const nextSpecial = remaining.search(/\*\*|`|\n/);
        if (nextSpecial === -1) {
            parts.push({ type: 'text', content: remaining });
            break;
        } else if (nextSpecial > 0) {
            parts.push({ type: 'text', content: remaining.slice(0, nextSpecial) });
            remaining = remaining.slice(nextSpecial);
        } else {
            // Edge case: special char at start but didn't match pattern
            parts.push({ type: 'text', content: remaining[0] });
            remaining = remaining.slice(1);
        }
    }
    
    return parts;
}

function stripForSpeech(text) {
    // Remove markdown and emojis for text-to-speech
    return text
        .replace(/\*\*/g, '')
        .replace(/[📞📋🔍🗑️📊↙️↗️✗🎤]/g, '')
        .trim();
}

async function sendMessage(text) {
    if (!text.trim()) return;
    
    // Add user message to chat
    addMessage(text, true);
    textInput.value = '';
    
    // Update synthesis panel - show thinking state
    reasoningText.textContent = 'Thinking...';
    actionText.textContent = 'Processing...';
    dataPreview.textContent = 'Loading...';
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            // Add assistant response to chat
            addMessage(result.response);
            
            // Update synthesis panel
            reasoningText.textContent = result.reasoning || 'No reasoning provided';
            actionText.textContent = result.action_taken || 'None';
            
            if (result.data) {
                dataPreview.textContent = JSON.stringify(result.data, null, 2);
            } else {
                dataPreview.textContent = 'No data retrieved';
            }
            
            // Speak the response
            speak(stripForSpeech(result.response));
            
            // Refresh calls list if action involved calls
            if (['listed_calls', 'deleted_call', 'searched_calls'].includes(result.action_taken)) {
                loadCalls();
            }
        } else {
            addMessage(`Error: ${result.error || 'Something went wrong'}`);
            reasoningText.textContent = 'Error occurred';
            actionText.textContent = 'Failed';
            dataPreview.textContent = JSON.stringify(result, null, 2);
        }
    } catch (error) {
        console.error('Chat error:', error);
        addMessage('Sorry, I encountered a connection error. Please try again.');
        reasoningText.textContent = 'Connection error';
        actionText.textContent = 'Failed';
        dataPreview.textContent = error.message;
    }
}

// ─── Calls Management ─────────────────────────────────────────────────────────

async function loadCalls() {
    try {
        const response = await fetch('/api/calls');
        const calls = await response.json();
        
        if (calls.length === 0) {
            callsList.innerHTML = '<p class="empty-state">No calls logged yet. Add your first call!</p>';
            return;
        }
        
        callsList.innerHTML = calls.map(call => `
            <div class="call-item" data-id="${call.id}">
                <div class="call-direction ${call.direction}">
                    ${call.direction === 'incoming' ? '↙️' : call.direction === 'outgoing' ? '↗️' : '✗'}
                </div>
                <div class="call-info">
                    <div class="call-name">${escapeHtml(call.contact_name)}</div>
                    <div class="call-details">
                        ${escapeHtml(call.phone_number)} · 
                        ${formatDuration(call.duration_seconds)} · 
                        ${formatTimestamp(call.timestamp)}
                        ${call.notes ? ` · <em>${escapeHtml(call.notes)}</em>` : ''}
                    </div>
                </div>
                <div class="call-actions">
                    <button class="btn-sm danger" onclick="deleteCall(${call.id})">🗑️</button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Failed to load calls:', error);
        callsList.innerHTML = '<p class="empty-state">Failed to load calls</p>';
    }
}

async function deleteCall(id) {
    if (!confirm('Delete this call record?')) return;
    
    try {
        const response = await fetch(`/api/calls/${id}`, { method: 'DELETE' });
        if (response.ok) {
            loadCalls();
        }
    } catch (error) {
        console.error('Failed to delete call:', error);
    }
}

async function addCall(event) {
    event.preventDefault();
    
    const data = {
        contact_name: document.getElementById('callName').value,
        phone_number: document.getElementById('callNumber').value,
        direction: document.getElementById('callDirection').value,
        duration_seconds: document.getElementById('callDuration').value || null,
        notes: document.getElementById('callNotes').value,
    };
    
    try {
        const response = await fetch('/api/calls', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            addCallModal.classList.remove('active');
            addCallForm.reset();
            loadCalls();
            addMessage(`✓ Added call from ${data.contact_name}`);
        } else {
            const result = await response.json();
            alert(result.error || 'Failed to add call');
        }
    } catch (error) {
        console.error('Failed to add call:', error);
        alert('Failed to add call');
    }
}

// ─── Identity Management ──────────────────────────────────────────────────────

async function updateIdentity(event) {
    event.preventDefault();
    
    const data = {
        name: document.getElementById('identityName').value,
        role: document.getElementById('identityRole').value,
        personality: document.getElementById('identityPersonality').value,
        greeting: document.getElementById('identityGreeting').value,
        voice: document.getElementById('identityVoice').value,
    };
    
    try {
        const response = await fetch('/api/identity', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            const identity = await response.json();
            assistantName.textContent = identity.name;
            assistantRole.textContent = identity.role;
            settingsModal.classList.remove('active');
            addMessage(`My identity has been updated! I'm now ${identity.name}.`);
        }
    } catch (error) {
        console.error('Failed to update identity:', error);
    }
}

// ─── Utility Functions ────────────────────────────────────────────────────────

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDuration(seconds) {
    if (seconds === null || seconds === undefined) return '-';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    if (mins > 0) return `${mins}m ${secs}s`;
    return `${secs}s`;
}

function formatTimestamp(isoString) {
    const date = new Date(isoString);
    return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit'
    });
}

// ─── Event Listeners ──────────────────────────────────────────────────────────

micBtn.addEventListener('click', () => {
    if (isListening) {
        recognition?.stop();
    } else {
        startListening();
    }
});

sendBtn.addEventListener('click', () => {
    sendMessage(textInput.value);
});

textInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendMessage(textInput.value);
    }
});

// Settings modal
settingsBtn.addEventListener('click', () => settingsModal.classList.add('active'));
closeSettingsBtn.addEventListener('click', () => settingsModal.classList.remove('active'));
identityForm.addEventListener('submit', updateIdentity);

// Add call modal
addCallBtn.addEventListener('click', () => addCallModal.classList.add('active'));
closeAddCallBtn.addEventListener('click', () => addCallModal.classList.remove('active'));
addCallForm.addEventListener('submit', addCall);

// Close modals on background click
[settingsModal, addCallModal].forEach(modal => {
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.remove('active');
        }
    });
});

// ─── Initialize ───────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    loadCalls();
    
    // Load voices for speech synthesis
    if ('speechSynthesis' in window) {
        window.speechSynthesis.onvoiceschanged = () => {
            window.speechSynthesis.getVoices();
        };
    }
});
