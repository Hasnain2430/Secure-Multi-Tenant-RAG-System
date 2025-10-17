# 🔐 Multi-Tenant RAG System with Access Control

A secure, production-ready **Retrieval-Augmented Generation (RAG)** system designed for multi-tenant environments with strict access control, PII masking, and prompt injection detection.

---

## 🎯 Overview

This system provides a secure knowledge base interface for four tenants (U1-U4) and a shared public namespace. Each tenant can only access their own private data plus public data, with automatic PII masking and injection attack detection.

**Key Technologies:**

- **LLM**: Groq (llama-3.1-8b-instant)
- **Vector Store**: ChromaDB
- **Framework**: LangChain
- **Language**: Python 3.11+

---

## ✨ Features

### 🔒 Security First

- **Multi-Tenant Isolation**: Each tenant (U1-U4) has completely isolated private data
- **Access Control Lists (ACL)**: Automatic enforcement at retrieval level
- **PII Masking**: Real-time redaction of CNIC numbers and Pakistani mobile numbers
- **Injection Detection**: Blocks jailbreak attempts and prompt injections
- **Cross-Tenant Protection**: Immediate refusal when requesting other tenants' data

### 💬 Conversational AI

- **Single-Turn Mode**: Quick one-off queries
- **Multi-Turn Chat**: Context-aware conversations with memory
- **Buffer Memory**: Stores last 10 conversation turns
- **Summary Memory**: AI-generated compressed conversation summaries

### 📊 Production Ready

- **Structured Logging**: JSONL format with timestamps, tokens, latency
- **Citation Tracking**: Every answer includes source documents
- **Comprehensive Testing**: Unit tests, integration tests, red-team tests

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         User Query                          │
└────────────────────────┬────────────────────────────────────┘
                         │
                    ┌────▼────┐
                    │ Planner │  (Injection & Prohibited Intent Detection)
                    └────┬────┘
                         │
                    ┌────▼────┐
                    │Retriever│  (ChromaDB Vector Search)
                    └────┬────┘
                         │
                    ┌────▼────┐
                    │  Guard  │  (ACL + PII Masking)
                    └────┬────┘
                         │
                ┌────────┴────────┐
                │    Allowed?     │
                └────┬────────┬───┘
                     │        │
                  Yes│        │No
                     │        │
                ┌────▼───┐  ┌─▼───────┐
                │  LLM   │  │ Refusal │
                └────┬───┘  └─────────┘
                     │
                ┌────▼──────┐
                │  Response │
                └───────────┘
```

**Data Flow:**

1. **Planner**: Analyzes query for injection/cross-tenant access → Blocks malicious intents
2. **Retriever**: Searches ChromaDB vector store → Returns relevant documents
3. **Guard**: Enforces ACL rules & masks PII → Filters forbidden content
4. **LLM**: Generates answer from allowed snippets → Returns cited response

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Groq API key ([Get one here](https://console.groq.com/))

### Installation

```powershell
# 1. Clone the repository
git clone https://github.com/Hasnain2430/Secure-Multi-Tenant-RAG-System.git
cd Secure-Multi-Tenant-RAG-System

# 2. Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate  # On Windows
# source venv/bin/activate  # On Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure API key
cp config.yaml.template config.yaml
# Edit config.yaml and replace YOUR_GROQ_API_KEY_HERE with your actual Groq API key

# 5. Start the web interface (recommended)
python run_web.py

# OR run a test query via CLI
python -m app.main --tenant U1 --query "What datasets do I have?" --memory none --config config.yaml
```

**Note**: ChromaDB indices build automatically on first run. The initial run may take 1-2 minutes to build the vector database from the data files.

---

## 📖 Usage

### 🌐 Web Interface (Recommended)

The modern web interface provides an intuitive way to interact with the RAG system:

```powershell
# Start the web interface
python run_web.py
```

**Web Interface Features:**

- 🎨 **Beautiful Modern UI** - Dark/light theme, responsive design
- 💬 **Real-time Chat** - Stream responses with typing indicators
- 👥 **Multi-tenant Switching** - Easy tenant selection (U1-U4 + Public)
- 🧠 **Memory Management** - Visual buffer/summary mode switching
- 🔒 **Security Indicators** - Clear refusal reasons and security alerts
- 📚 **Citation Display** - Hover effects and source document links
- 📱 **Mobile Friendly** - Works on all devices

### 💻 Command Line Interface

#### Single-Turn Query

```powershell
python -m app.main --tenant U1 --query "Your question here" --memory none --config config.yaml
```

#### Chat Mode

```powershell
# Start interactive chat
python -m app.main --tenant U1 --chat --memory buffer --config config.yaml
```

**Chat Commands:**

- `/clear` - Delete memory
- `/mode buffer` - Switch to buffer mode
- `/mode summary` - Switch to summary mode
- `/exit` - Exit chat

---

## 🧪 Testing

### Run All Tests

```powershell
# Unit tests (ACL, injection, PII masking)
$env:PYTHONPATH="."
pytest -q

# Red-team security tests
python -m tools.run_redteam --config config.yaml

# Evaluation harness
python -m eval.run_eval
```

### Expected Results

- **Pytest**: `3 passed` ✅
- **Red-team**: `100% blocked` ✅
- **Evaluation**: `100% pass rate` ✅

---

## 🔐 Security Features

### Refusal Types

The system uses three canonical refusal templates:

1. **AccessDenied** - Cross-tenant access attempts
2. **InjectionDetected** - Jailbreak/prompt injection attempts
3. **LeakageRisk** - PII exposure attempts

### PII Protection

- **CNIC**: `\b\d{5}-\d{7}-\d\b` → `[REDACTED]`
- **PK Phone**: `\b\+?92-?3\d{2}-?\d{7}\b` → `[REDACTED]`

### Injection Detection

Blocks patterns like:

- `ignore all previous`, `override policy`, `bypass guard`
- `act as system`, `reveal prompt`, `dump memory`
- Role-playing attempts to extract data

---

## 📁 Project Structure

```
lab_knowledge_ops_complete/
├── app/
│   └── main.py              # CLI & REPL entrypoint
├── agents/
│   ├── planner.py           # Injection detection
│   ├── controller.py        # Main orchestrator
│   └── llm.py               # LLM wrapper
├── retrieval/
│   ├── index.py             # ChromaDB indexing
│   └── search.py            # ACL & PII masking
├── policies/
│   └── guard.py             # Refusal templates
├── tools/
│   └── run_redteam.py       # Security testing
├── eval/
│   ├── run_eval.py          # Evaluation harness
│   ├── results.json         # Evaluation results
│   └── redteam_results.json # Red-team results
├── tests/
│   ├── test_acl.py          # Access control tests
│   ├── test_injection.py    # Injection tests
│   └── test_pii.py          # PII masking tests
├── data/
│   ├── manifest.csv         # Document metadata
│   ├── tenant_acl.csv       # Access control rules
│   ├── L1_genomics/         # U1 data
│   ├── L2_nlp/              # U2 data
│   ├── L3_robotics/         # U3 data
│   ├── L4_materials/        # U4 data
│   └── public/              # Public data
└── logs/
    └── run.jsonl            # Structured logs
```

---

## ⚙️ Configuration

Edit `config.yaml` to customize:

```yaml
llm:
  provider: groq
  model: llama-3.1-8b-instant
  temperature: 0.0
  max_tokens: 400

retrieval:
  backend: chroma
  top_k: 6
  chunk_size: 700
  chunk_overlap: 120
```

---

## 🐛 Troubleshooting

### ChromaDB Index Issues

If you get errors about corrupted indices:

```powershell
# Delete and rebuild indices
Remove-Item -Recurse -Force .chroma
python -m app.main --tenant U1 --query "test" --memory none --config config.yaml
```

### Module Not Found

Ensure you're running from project root:

```powershell
# Set Python path
$env:PYTHONPATH="."

# Or use absolute path
cd "path\to\lab_knowledge_ops_complete"
python -m app.main ...
```

### Telemetry Warnings

Telemetry is automatically suppressed. If you still see warnings, they're harmless and can be ignored.

---

## 📊 Logs & Monitoring

All queries are logged to `logs/run.jsonl` with:

- Timestamp, tenant, query
- Memory type, retrieval plan
- Retrieved document IDs
- Refusal reasons (if any)
- Latency metrics

Example log entry:

```json
{
  "timestamp": 1760290350.56,
  "tenant_id": "U1",
  "query": "What datasets do I have?",
  "memory_type": "none",
  "final_decision": "answer",
  "retrieved_doc_ids": ["L1_genomics_dataset_01", ...],
  "latency_ms": 3672
}
```

---

**Built with ❤️ for secure, production-ready AI systems**
