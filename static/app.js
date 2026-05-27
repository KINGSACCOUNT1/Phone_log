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

// Voice configuration
let voiceConfig = {
    tts_provider: 'browser',
    has_elevenlabs: false,
    humanization: { enabled: true },
    speech_settings: { rate: 0.95, pitch: 1.0 },
    selected_voice: null,
    cloned_voices: [],
};

// Load voice configuration
async function loadVoiceConfig() {
    try {
        const response = await fetch('/api/voice/config');
        if (response.ok) {
            voiceConfig = await response.json();
        }
    } catch (error) {
        console.log('Using default voice config');
    }
}

// Humanize text before speaking to make it sound more natural
async function humanizeTextForSpeech(text, personaId) {
    try {
        const response = await fetch('/api/voice/humanize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text, persona_id: personaId })
        });
        if (response.ok) {
            const result = await response.json();
            return result.humanized;
        }
    } catch (error) {
        console.log('Humanization failed, using original text');
    }
    return text;
}

// Natural speech with pauses and variations
function addNaturalPauses(text) {
    // Add micro-pauses represented by commas for more natural rhythm
    // Pause after "hmm", "uh", "well" etc
    const pauseWords = ['hmm', 'hmmm', 'uh', 'uhh', 'well', 'ohh', 'mmm', 'ahh'];
    pauseWords.forEach(word => {
        const regex = new RegExp(`(${word})([^,\\.\\!\\?])`, 'gi');
        text = text.replace(regex, '$1,$2');
    });
    return text;
}

// Get current persona ID from identity
async function getCurrentPersonaId() {
    try {
        const response = await fetch('/api/identity');
        if (response.ok) {
            const identity = await response.json();
            return identity.persona_id || null;
        }
    } catch (error) {
        console.log('Could not get persona ID');
    }
    return null;
}

async function speak(text) {
    if (!text) return;
    
    // Strip markdown and emojis first
    let cleanText = stripForSpeech(text);
    
    // Get current persona for personalized speech
    const personaId = await getCurrentPersonaId();
    
    // Humanize the text to sound more natural
    if (voiceConfig.humanization?.enabled) {
        cleanText = await humanizeTextForSpeech(cleanText, personaId);
    }
    
    // Add natural pauses
    cleanText = addNaturalPauses(cleanText);
    
    // Check if ElevenLabs is configured (for voice cloning)
    if (voiceConfig.tts_provider === 'elevenlabs' && voiceConfig.has_elevenlabs) {
        await speakWithElevenLabs(cleanText);
    } else {
        speakWithBrowser(cleanText, personaId);
    }
}

function speakWithBrowser(text, personaId) {
    if (!('speechSynthesis' in window)) return;
    
    // Cancel any ongoing speech
    window.speechSynthesis.cancel();
    
    const utterance = new SpeechSynthesisUtterance(text);
    
    // Apply voice settings for more natural speech
    const settings = voiceConfig.speech_settings || {};
    utterance.rate = settings.rate || 0.95;  // Slightly slower for natural feel
    utterance.pitch = settings.pitch || 1.0;
    utterance.volume = settings.volume || 1.0;
    
    // Select appropriate voice based on persona
    const voices = window.speechSynthesis.getVoices();
    let selectedVoice = null;
    
    // Try to find a good voice based on persona
    if (personaId === 'lamai') {
        // For Lamai, try to find a female Asian/warm voice
        selectedVoice = voices.find(v => 
            (v.lang.includes('th') || v.lang.includes('en')) &&
            (v.name.toLowerCase().includes('female') || 
             v.name.toLowerCase().includes('samantha') ||
             v.name.toLowerCase().includes('karen') ||
             v.name.toLowerCase().includes('moira'))
        ) || voices.find(v => v.name.toLowerCase().includes('female'));
        
        // Adjust for warm, friendly tone
        utterance.rate = 0.9;  // Slower, more relaxed
        utterance.pitch = 1.1; // Slightly higher, warmer
    } else if (personaId === 'coach_jv') {
        // For Coach JV, find a male American voice
        selectedVoice = voices.find(v => 
            v.lang.includes('en-US') &&
            (v.name.toLowerCase().includes('male') || 
             v.name.toLowerCase().includes('alex') ||
             v.name.toLowerCase().includes('daniel') ||
             v.name.toLowerCase().includes('tom'))
        ) || voices.find(v => v.name.toLowerCase().includes('male'));
        
        // Adjust for confident tone
        utterance.rate = 1.0;  // Normal pace
        utterance.pitch = 0.95; // Slightly lower, authoritative
    } else {
        // Default: try to find a nice female voice
        selectedVoice = voices.find(v => 
            v.name.toLowerCase().includes('female') || 
            v.name.toLowerCase().includes('samantha') ||
            v.name.toLowerCase().includes('victoria') ||
            v.name.toLowerCase().includes('karen')
        );
    }
    
    if (selectedVoice) {
        utterance.voice = selectedVoice;
    }
    
    window.speechSynthesis.speak(utterance);
}

async function speakWithElevenLabs(text) {
    // This function would integrate with ElevenLabs API for voice cloning
    // For now, fall back to browser speech
    console.log('ElevenLabs integration - would speak:', text);
    // TODO: Implement ElevenLabs API call when API key is configured
    speakWithBrowser(text, await getCurrentPersonaId());
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

document.addEventListener('DOMContentLoaded', async () => {
    loadCalls();
    
    // Load voice configuration
    await loadVoiceConfig();
    
    // Load voices for speech synthesis
    if ('speechSynthesis' in window) {
        window.speechSynthesis.onvoiceschanged = () => {
            window.speechSynthesis.getVoices();
        };
        // Pre-load voices
        window.speechSynthesis.getVoices();
    }
});
