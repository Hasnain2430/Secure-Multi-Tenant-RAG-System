"""
Flask Web Application for Secure Multi-Tenant RAG System
Beautiful, modern frontend with real-time chat interface
"""

from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO
import json
import os
import sys
import time
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.controller import agent_with_metadata
from app.main import load_memory, persist_memory

app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global state for each user session
user_sessions = {}

class UserSession:
    def __init__(self, user_id):
        self.user_id = user_id
        self.tenant = "U1"
        self.memory_type = "buffer"
        self.memory = None
        self.chat_history = []
        self.is_processing = False

    def switch_tenant(self, new_tenant):
        self.tenant = new_tenant
        self.memory = None
        self.chat_history = []
        self.load_memory()

    def load_memory(self):
        try:
            self.memory = load_memory(self.tenant, self.memory_type)
        except:
            self.memory = None

    def persist_memory(self):
        try:
            persist_memory(self.tenant, self.memory_type, self.memory)
        except:
            pass

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/switch_tenant', methods=['POST'])
def switch_tenant():
    data = request.get_json()
    tenant = data.get('tenant', 'U1')
    
    if 'user_id' not in session:
        session['user_id'] = f"user_{int(time.time())}"
    
    user_id = session['user_id']
    
    if user_id not in user_sessions:
        user_sessions[user_id] = UserSession(user_id)
    
    user_sessions[user_id].switch_tenant(tenant)
    
    return jsonify({
        'status': 'success',
        'tenant': tenant,
        'message': f'Switched to {tenant}'
    })

@app.route('/api/switch_memory', methods=['POST'])
def switch_memory():
    data = request.get_json()
    memory_type = data.get('memory_type', 'buffer')
    
    if 'user_id' not in session:
        session['user_id'] = f"user_{int(time.time())}"
    
    user_id = session['user_id']
    
    if user_id not in user_sessions:
        user_sessions[user_id] = UserSession(user_id)
    
    user_sessions[user_id].memory_type = memory_type
    user_sessions[user_id].load_memory()
    
    return jsonify({
        'status': 'success',
        'memory_type': memory_type,
        'message': f'Switched to {memory_type} memory'
    })

@app.route('/api/clear_memory', methods=['POST'])
def clear_memory():
    if 'user_id' not in session:
        session['user_id'] = f"user_{int(time.time())}"
    
    user_id = session['user_id']
    
    if user_id not in user_sessions:
        user_sessions[user_id] = UserSession(user_id)
    
    user_sessions[user_id].memory = None
    user_sessions[user_id].chat_history = []
    user_sessions[user_id].persist_memory()
    
    return jsonify({
        'status': 'success',
        'message': 'Memory cleared'
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    query = data.get('query', '').strip()
    
    if not query:
        return jsonify({'error': 'Empty query'}), 400
    
    if 'user_id' not in session:
        session['user_id'] = f"user_{int(time.time())}"
    
    user_id = session['user_id']
    
    if user_id not in user_sessions:
        user_sessions[user_id] = UserSession(user_id)
    
    session_obj = user_sessions[user_id]
    
    if session_obj.is_processing:
        return jsonify({'error': 'Already processing a request'}), 429
    
    session_obj.is_processing = True
    
    try:
        # Add user message to history
        user_message = {
            'type': 'user',
            'content': query,
            'timestamp': datetime.now().isoformat()
        }
        session_obj.chat_history.append(user_message)
        
        # Process the query
        start_time = time.time()
        result = agent_with_metadata(
            query=query,
            tenant_id=session_obj.tenant,
            memory=session_obj.memory,
            config_path="config.yaml"
        )
        processing_time = time.time() - start_time
        
        # Update memory
        session_obj.memory = result.get('memory', session_obj.memory)
        session_obj.persist_memory()
        
        # Add assistant response to history
        assistant_message = {
            'type': 'assistant',
            'content': result['output'],
            'metadata': {
                'plan': result.get('plan', {}),
                'retrieved_doc_ids': result.get('retrieved_doc_ids', []),
                'final_decision': result.get('final_decision', ''),
                'refusal_reason': result.get('refusal_reason', ''),
                'latency_ms': result.get('latency_ms', 0),
                'processing_time': processing_time
            },
            'timestamp': datetime.now().isoformat()
        }
        session_obj.chat_history.append(assistant_message)
        
        return jsonify({
            'status': 'success',
            'response': result['output'],
            'metadata': assistant_message['metadata'],
            'chat_history': session_obj.chat_history[-10:]  # Last 10 messages
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error processing query: {str(e)}'
        }), 500
    
    finally:
        session_obj.is_processing = False

@app.route('/api/status')
def status():
    if 'user_id' not in session:
        return jsonify({'status': 'no_session'})
    
    user_id = session['user_id']
    
    if user_id not in user_sessions:
        return jsonify({'status': 'no_session'})
    
    session_obj = user_sessions[user_id]
    
    return jsonify({
        'status': 'active',
        'tenant': session_obj.tenant,
        'memory_type': session_obj.memory_type,
        'is_processing': session_obj.is_processing,
        'chat_count': len(session_obj.chat_history)
    })

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('logs', exist_ok=True)
    os.makedirs('.state/memory', exist_ok=True)
    
    print("🚀 Starting Secure Multi-Tenant RAG Web Interface...")
    print("📱 Open your browser and go to: http://localhost:5000")
    print("🔒 Secure, modern interface with real-time chat")
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)