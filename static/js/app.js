// Modern JavaScript for Secure RAG System
class RAGApp {
    constructor() {
        this.currentTenant = 'U1';
        this.currentMemory = 'buffer';
        this.isProcessing = false;
        this.chatHistory = [];
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadSession();
        this.updateUI();
    }

    setupEventListeners() {
        // Chat input handling
        const chatInput = document.getElementById('chat-input');
        chatInput.addEventListener('input', this.handleInputChange.bind(this));
        
        // Send button
        document.getElementById('send-btn').addEventListener('click', this.sendMessage.bind(this));
        
        // Example query clicks
        document.addEventListener('click', (e) => {
            if (e.target.matches('.example-queries li')) {
                chatInput.value = e.target.textContent;
                this.handleInputChange();
                this.sendMessage();
            }
        });
    }

    handleInputChange() {
        const input = document.getElementById('chat-input');
        const sendBtn = document.getElementById('send-btn');
        
        // Auto-resize textarea
        input.style.height = 'auto';
        input.style.height = Math.min(input.scrollHeight, 120) + 'px';
        
        // Enable/disable send button
        sendBtn.disabled = !input.value.trim() || this.isProcessing;
    }

    handleKeyDown(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            this.sendMessage();
        }
    }

    autoResize(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    }

    async sendMessage() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();
        
        if (!message || this.isProcessing) return;
        
        this.isProcessing = true;
        this.updateUI();
        
        // Add user message to chat
        this.addMessage('user', message);
        
        // Clear input
        input.value = '';
        input.style.height = 'auto';
        this.handleInputChange();
        
        // Show loading
        this.showLoading();
        
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query: message })
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                this.addMessage('assistant', data.response, data.metadata);
                this.updateSessionInfo(data.chat_history?.length || 0);
            } else {
                this.addMessage('assistant', `Error: ${data.message}`, null, 'error');
            }
            
        } catch (error) {
            this.addMessage('assistant', `Network error: ${error.message}`, null, 'error');
        } finally {
            this.hideLoading();
            this.isProcessing = false;
            this.updateUI();
        }
    }

    addMessage(type, content, metadata = null, messageType = 'normal') {
        const messagesContainer = document.getElementById('chat-messages');
        
        // Remove welcome message if it exists
        const welcomeMessage = messagesContainer.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = type === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        if (type === 'assistant') {
            contentDiv.className += ` ${messageType}`;
        }
        
        // Add content
        contentDiv.innerHTML = this.formatContent(content);
        
        // Add metadata if available
        if (metadata && type === 'assistant') {
            const metaDiv = document.createElement('div');
            metaDiv.className = 'message-meta';
            
            if (metadata.final_decision === 'refuse') {
                metaDiv.innerHTML = `<i class="fas fa-shield-alt"></i> ${metadata.refusal_reason || 'Request blocked'}`;
            } else if (metadata.retrieved_doc_ids && metadata.retrieved_doc_ids.length > 0) {
                metaDiv.innerHTML = `<i class="fas fa-search"></i> Retrieved ${metadata.retrieved_doc_ids.length} documents`;
            } else {
                metaDiv.innerHTML = `<i class="fas fa-clock"></i> ${metadata.latency_ms || 0}ms`;
            }
            
            contentDiv.appendChild(metaDiv);
            
            // Add citations if available
            if (metadata.retrieved_doc_ids && metadata.retrieved_doc_ids.length > 0) {
                const citationsDiv = document.createElement('div');
                citationsDiv.className = 'citations';
                citationsDiv.innerHTML = '<h4>Sources:</h4>';
                
                metadata.retrieved_doc_ids.forEach(docId => {
                    const citation = document.createElement('span');
                    citation.className = 'citation';
                    citation.textContent = docId;
                    citation.title = `Document: ${docId}`;
                    citationsDiv.appendChild(citation);
                });
                
                contentDiv.appendChild(citationsDiv);
            }
        }
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(contentDiv);
        messagesContainer.appendChild(messageDiv);
        
        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        // Store in history
        this.chatHistory.push({
            type,
            content,
            metadata,
            timestamp: new Date().toISOString()
        });
    }

    formatContent(content) {
        // Basic markdown-like formatting
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
    }

    async switchTenant(tenant) {
        if (this.isProcessing) return;
        
        this.currentTenant = tenant;
        
        // Update UI
        document.querySelectorAll('.tenant-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-tenant="${tenant}"]`).classList.add('active');
        
        // Update chat title
        const titles = {
            'U1': 'Chat with U1 Genomics',
            'U2': 'Chat with U2 NLP',
            'U3': 'Chat with U3 Robotics',
            'U4': 'Chat with U4 Materials',
            'public': 'Chat with Public Data'
        };
        document.getElementById('chat-title').textContent = titles[tenant] || `Chat with ${tenant}`;
        
        // Clear chat messages and show welcome
        const messagesContainer = document.getElementById('chat-messages');
        messagesContainer.innerHTML = `
            <div class="welcome-message">
                <div class="welcome-content">
                    <i class="fas fa-robot"></i>
                    <h3>Welcome to ${tenant}</h3>
                    <p>Ask me anything about your data! I can help you explore datasets, answer questions, and provide insights.</p>
                    <div class="example-queries">
                        <h4>Try asking:</h4>
                        <ul>
                            <li>"What datasets do I have?"</li>
                            <li>"Tell me about the first dataset"</li>
                            <li>"What safety protocols are required?"</li>
                        </ul>
                    </div>
                </div>
            </div>
        `;
        
        // Reset chat history
        this.chatHistory = [];
        
        // Update session info
        this.updateSessionInfo(0);
        
        // Notify server
        try {
            await fetch('/api/switch_tenant', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ tenant })
            });
        } catch (error) {
            this.showToast('Failed to switch tenant', 'error');
        }
    }

    async switchMemory(memoryType) {
        if (this.isProcessing) return;
        
        this.currentMemory = memoryType;
        
        // Update UI
        document.querySelectorAll('.memory-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-type="${memoryType}"]`).classList.add('active');
        
        // Update session info
        document.getElementById('current-memory').textContent = memoryType.charAt(0).toUpperCase() + memoryType.slice(1);
        
        // Notify server
        try {
            await fetch('/api/switch_memory', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ memory_type: memoryType })
            });
            this.showToast(`Switched to ${memoryType} memory`, 'success');
        } catch (error) {
            this.showToast('Failed to switch memory type', 'error');
        }
    }

    async clearMemory() {
        if (this.isProcessing) return;
        
        if (!confirm('Are you sure you want to clear all memory? This action cannot be undone.')) {
            return;
        }
        
        try {
            await fetch('/api/clear_memory', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            // Clear chat messages and show welcome
            const messagesContainer = document.getElementById('chat-messages');
            messagesContainer.innerHTML = `
                <div class="welcome-message">
                    <div class="welcome-content">
                        <i class="fas fa-robot"></i>
                        <h3>Memory Cleared</h3>
                        <p>All conversation history has been cleared. Start a new conversation!</p>
                    </div>
                </div>
            `;
            
            // Reset chat history
            this.chatHistory = [];
            this.updateSessionInfo(0);
            
            this.showToast('Memory cleared successfully', 'success');
        } catch (error) {
            this.showToast('Failed to clear memory', 'error');
        }
    }

    updateUI() {
        const sendBtn = document.getElementById('send-btn');
        const chatInput = document.getElementById('chat-input');
        
        sendBtn.disabled = !chatInput.value.trim() || this.isProcessing;
        
        // Update status
        const statusElement = document.getElementById('chat-status');
        if (this.isProcessing) {
            statusElement.innerHTML = '<i class="fas fa-circle"></i><span>Processing...</span>';
            statusElement.style.color = 'var(--warning)';
        } else {
            statusElement.innerHTML = '<i class="fas fa-circle"></i><span>Ready</span>';
            statusElement.style.color = 'var(--success)';
        }
    }

    updateSessionInfo(messageCount) {
        document.getElementById('current-tenant').textContent = this.currentTenant;
        document.getElementById('current-memory').textContent = this.currentMemory.charAt(0).toUpperCase() + this.currentMemory.slice(1);
        document.getElementById('message-count').textContent = messageCount;
    }

    showLoading() {
        document.getElementById('loading-overlay').classList.add('show');
    }

    hideLoading() {
        document.getElementById('loading-overlay').classList.remove('show');
    }

    showToast(message, type = 'success') {
        const toast = document.getElementById('toast');
        const icon = toast.querySelector('.toast-icon');
        const messageEl = toast.querySelector('.toast-message');
        
        // Set icon based on type
        const icons = {
            success: '<i class="fas fa-check-circle"></i>',
            error: '<i class="fas fa-exclamation-circle"></i>',
            warning: '<i class="fas fa-exclamation-triangle"></i>'
        };
        
        icon.innerHTML = icons[type] || icons.success;
        messageEl.textContent = message;
        
        // Set class for styling
        toast.className = `toast ${type}`;
        
        // Show toast
        toast.classList.add('show');
        
        // Hide after 3 seconds
        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    }

    loadSession() {
        // Load any existing session data
        this.updateSessionInfo(0);
    }
}

// Theme toggle functionality
function toggleTheme() {
    const body = document.body;
    const themeIcon = document.getElementById('theme-icon');
    
    if (body.getAttribute('data-theme') === 'dark') {
        body.removeAttribute('data-theme');
        themeIcon.className = 'fas fa-moon';
    } else {
        body.setAttribute('data-theme', 'dark');
        themeIcon.className = 'fas fa-sun';
    }
}

// Global functions for HTML onclick handlers
function switchTenant(tenant) {
    window.ragApp.switchTenant(tenant);
}

function switchMemory(memoryType) {
    window.ragApp.switchMemory(memoryType);
}

function clearMemory() {
    window.ragApp.clearMemory();
}

function sendMessage() {
    window.ragApp.sendMessage();
}

function handleKeyDown(event) {
    window.ragApp.handleKeyDown(event);
}

function autoResize(textarea) {
    window.ragApp.autoResize(textarea);
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.ragApp = new RAGApp();
});