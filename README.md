<div align="center">

# 🛡️ Elder AI Guardian

### *Protecting Our Elders with the Power of Microsoft AI*

[![Microsoft Azure](https://img.shields.io/badge/Microsoft_Azure-0078D4?style=for-the-badge&logo=microsoft-azure&logoColor=white)](https://azure.microsoft.com)
[![GPT-4o](https://img.shields.io/badge/GPT--4o-412991?style=for-the-badge&logo=openai&logoColor=white)](https://azure.microsoft.com/en-us/products/ai-services/openai-service)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React_18-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://reactjs.org)
[![Semantic Kernel](https://img.shields.io/badge/Semantic_Kernel-5C2D91?style=for-the-badge&logo=microsoft&logoColor=white)](https://aka.ms/semantic-kernel)

**Microsoft AI Dev Days Hackathon 2026** · Built solo in 48 hours

[🎬 Demo Video](#demo) · [🏗️ Architecture](#architecture) · [🚀 Quick Start](#quick-start) · [📡 API Reference](#api-reference)

---

> *Every 11 seconds, an elder falls. Every year, $3 billion is lost to elder scams. 125,000 Americans die from medication errors. Elder AI Guardian fights all three — with 6 specialized AI agents, real-time alerts, and the full power of Microsoft Azure.*

</div>

---

## 📋 Table of Contents

- [The Problem](#the-problem)
- [The Solution](#the-solution)
- [Hero Technologies](#hero-technologies)
- [Architecture](#architecture)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Azure Services](#azure-services)
- [Agent System](#agent-system)
- [Quick Start](#quick-start)
- [API Reference](#api-reference)
- [Project Structure](#project-structure)
- [Demo](#demo)

---

## 🚨 The Problem

The global elderly population faces a silent crisis that technology has largely ignored:

| Crisis | Scale | Current Solutions |
|--------|-------|-------------------|
| **Elder scam fraud** | $3 billion lost annually in the US | None — elders are left to fend for themselves |
| **Medication non-adherence** | 125,000 deaths per year | Paper pill boxes, manual reminders |
| **Falls** | 1 every 11 seconds, #1 cause of injury death in elderly | Expensive wearables, no AI |
| **Isolation** | 28% of seniors live alone | No real-time family communication |
| **Emergency response** | Average 8-minute delay when elder can't call | Old-school medical alert buttons |

Existing solutions are fragmented, expensive, and don't leverage modern AI. **There is no unified, AI-powered guardian for our elders.**

---

## 💡 The Solution

**Elder AI Guardian** is a unified multi-agent AI platform that:

- 🤖 **Detects scams in real-time** — analyzes messages, emails, and calls with GPT-4o threat profiling
- 🆘 **Triggers instant emergency response** — one-touch SOS with GPS location sharing and automatic family + 911 notification
- 💊 **Manages medications** — AI-powered reminders, adherence tracking, and refill alerts
- 🏥 **Monitors wellness** — daily check-ins, health trend analysis, proactive family reports
- 👨‍👩‍👧 **Connects families** — real-time dashboard for family members, live alerts without page refresh
- 🔧 **Self-heals autonomously** — Agentic DevOps monitors system health and auto-recovers

All powered by **Microsoft Foundry, Azure MCP, Microsoft Agent Framework, and Agentic DevOps** — the four hero technologies of Microsoft AI Dev Days 2026.

---

## 🏆 Hero Technologies

This project was built specifically to demonstrate the four Microsoft hero technologies:

### 1. 🧠 Microsoft Foundry
- **Azure AI Foundry project**: `aiselderai9338`
- **GPT-4o deployment** with custom routing strategies per agent type
- **Model Router** with 5 intelligent routing strategies:
  - `emergency` → direct generation (temp 0.1) — fast, precise
  - `scam_detection` → chain of thought (temp 0.2) — reasoning-based
  - `medication` → structured extraction (temp 0.3) — JSON output
  - `wellness` → sentiment analysis (temp 0.7) — empathetic
  - `general` → conversational (temp 0.8) — natural dialogue
- **Foundry Agent** with 5 model configurations, dynamic selection based on task complexity

### 2. 🔌 Azure MCP (Model Context Protocol)
- **9 MCP tools** integrated for real-time data access:

| Tool | Purpose |
|------|---------|
| `search_scam_database` | Query community-reported scam database |
| `send_emergency_alert` | Dispatch emergency notifications |
| `get_medication_info` | Retrieve drug interaction data |
| `check_wellness_status` | Pull health metrics |
| `notify_family` | Send family alerts |
| `get_health_records` | Access medical history |
| `schedule_reminder` | Create medication reminders |
| `analyze_threat` | Deep scam threat analysis |
| `get_emergency_contacts` | Retrieve contact list |

- MCP tools exposed via WebSocket — agents call tools in real-time during conversations
- Phone number verification against community scam database via MCP

### 3. 🤝 Microsoft Agent Framework
- **Semantic Kernel** as the foundation
- **Supervisor Agent** implementing A2A (Agent-to-Agent) communication protocol
- **6 specialized agents** with capability-based routing:
  - Intent classification before routing
  - Context preservation across agent handoffs
  - Collaborative multi-agent scenarios (e.g., scam detected → simultaneously alert family agent + log to Cosmos)
- **AgentGroupChat** pattern for complex multi-step scenarios

### 4. ⚙️ Agentic DevOps
- **DevOps Agent** running as a background autonomous service
- Monitors: CPU usage, memory consumption, disk space, error rates, service health
- **Self-healing capabilities**:
  - CPU spike → automatic process throttling
  - Memory leak → cache flush and GC trigger
  - Service degradation → automatic reinitialisation
  - Error rate spike → alert + diagnostic report
- DevOps metrics exposed via `/api/metrics` endpoint
- Integrates with **Azure Application Insights** for telemetry

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER LAYER                                    │
│  React 18 + Vite                                                │
│  Dashboard · Chat · Emergency SOS · Scam Detection              │
│  Medication · Wellness · Family Portal · Hero Showcase          │
└──────────────┬──────────────────────────┬───────────────────────┘
               │ WebSocket (live)          │ REST API
               ▼                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                   FASTAPI BACKEND                               │
│  Python 3.11 · Uvicorn · JWT Auth · CORS · Rate limiting       │
│  /auth /dashboard /chat /emergency /scam /medication /wellness  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              SUPERVISOR AGENT (Microsoft Agent Framework)       │
│  Semantic Kernel · Intent Classification · A2A Protocol         │
│  GPT-4o via Azure Foundry · Context Management                 │
└──┬──────────┬──────────┬──────────┬──────────┬─────────────────┘
   │          │          │          │          │
   ▼          ▼          ▼          ▼          ▼
┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐
│Emer- │  │Scam  │  │Medi- │  │Well- │  │Family│  │DevOps│
│gency │  │Detec-│  │cation│  │ness  │  │Notif │  │Agent │
│Agent │  │tion  │  │Agent │  │Agent │  │Agent │  │      │
└──┬───┘  └──┬───┘  └──┬───┘  └──┬───┘  └──┬───┘  └──┬───┘
   │          │          │          │          │          │
   └──────────┴──────────┴──────────┴──────────┴──────────┘
                                    │
            ┌───────────────────────┼───────────────────────┐
            │                       │                       │
            ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────────┐  ┌──────────────────┐
│  Azure Cosmos DB│    │  Azure OpenAI GPT-4o│  │  Azure Commun.   │
│  14 containers  │    │  aiselderai9338      │  │  SMS · Calls     │
│  elderaidb      │    │  Model Router        │  │  +919497734880   │
└─────────────────┘    └─────────────────────┘  └──────────────────┘
┌─────────────────┐    ┌─────────────────────┐  ┌──────────────────┐
│  Azure Key Vault│    │  App Insights        │  │  Azure MCP       │
│  kvelderai9338  │    │  Live telemetry      │  │  9 tools         │
└─────────────────┘    └─────────────────────┘  └──────────────────┘
```

---

## ✨ Features

### 🆘 Emergency Response System
- **One-touch SOS** — large, accessible button with confirmation dialog
- **GPS location capture** — precise coordinates shared with emergency contacts
- **Auto-escalation** — Emergency Agent classifies severity (LOW/MEDIUM/HIGH/CRITICAL)
- **Real-time family notification** — family dashboard updates instantly via WebSocket
- **Emergency types** — Medical, Fire, Security, Fall Detection
- **Stepwise tracking** — Detected → Notifying → Dispatched → Resolved
- **Cosmos DB persistence** — every SOS event stored with full context

### 🛡️ AI Scam Detection
- **GPT-4o powered threat analysis** — reasoning-based, not just keyword matching
- **Threat profiling** — urgency level, emotional manipulation score, social engineering tactics
- **Risk levels** — LOW / MEDIUM / HIGH / CRITICAL with actionable recommendations
- **Scam type classification** — phishing, tech support, grandparent, lottery, romance, investment
- **Community database** — phone numbers checked against reported scam database via MCP
- **Educational tips** — each analysis includes personalized elder-specific guidance
- **Family notification** — HIGH/CRITICAL scams automatically alert family members

### 💊 Medication Management
- **AI medication extraction** — describe a medication in natural language, AI extracts name, dosage, frequency
- **Smart scheduling** — twice-daily reminders at 08:00 and 20:00 by default
- **Adherence tracking** — taken/missed logging with 7-day report
- **Refill alerts** — warns 7 days before medications run out
- **Family escalation** — low adherence (<70%) automatically notifies family
- **Cosmos DB storage** — full medication history persisted

### 🏥 Wellness Monitoring
- **Daily check-ins** — mood, pain, sleep, appetite tracking
- **Trend analysis** — GPT-4o identifies wellness patterns over time
- **Proactive reports** — AI generates weekly wellness summaries
- **Wellness tips** — personalized advice based on health data
- **Family dashboard** — wellness trends visible to family members

### 👨‍👩‍👧 Family Portal
- **Real-time dashboard** — live view of elder's activity without refreshing
- **Live alerts** — WebSocket push notifications for emergencies and scams
- **Alert subscription** — family members subscribe to specific elder's alerts
- **Emergency contacts** — manage and call emergency contacts directly
- **Pending alerts** — REST fallback for family members not on WebSocket

### 🤖 AI Chat Interface
- **Natural language** — chat with 6 specialized agents in plain English
- **Intent routing** — Supervisor Agent automatically routes to the right specialist
- **WebSocket-first** — real-time responses via WebSocket, REST fallback
- **Context preservation** — session-based conversation history
- **MCP tools display** — shows which tools were used for each response
- **Agent attribution** — each response shows which agent responded

### 📊 Hero Technologies Dashboard
- **Live status badges** — Foundry, MCP, Agent Framework, DevOps, Cosmos DB, Live Alerts
- **MCP tool count** — shows 9 available tools in real-time
- **System metrics** — uptime, active connections, request count
- **DevOps health** — CPU, memory, service status

---

## 🛠️ Tech Stack

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.11 | Core language |
| FastAPI | 0.100+ | REST API framework |
| Uvicorn | Latest | ASGI server |
| Semantic Kernel | Latest | Agent orchestration framework |
| azure-ai-projects | Latest | Azure Foundry integration |
| azure-ai-inference | Latest | GPT-4o calls |
| azure-cosmos | 4.15.0 | Database client |
| azure-communication-sms | Latest | SMS service |
| azure-communication-callautomation | Latest | Call automation |
| azure-monitor-opentelemetry | Latest | Application Insights |
| azure-keyvault-secrets | Latest | Key Vault client |
| python-jose | Latest | JWT authentication |
| pydantic | Latest | Data validation |

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| React | 18 | UI framework |
| Vite | Latest | Build tool |
| Material UI | 5 | Component library |
| Zustand | Latest | State management |
| React Query | Latest | Server state |
| Axios | Latest | HTTP client |
| Framer Motion | Latest | Animations |
| date-fns | Latest | Date formatting |

---

## ☁️ Azure Services

All services are **live and configured** — not mocked:

| Service | Resource Name | Region | Purpose |
|---------|--------------|--------|---------|
| **Azure AI Foundry** | `aiselderai9338` | East US | GPT-4o hosting, model routing |
| **Azure OpenAI** | `aiselderai9338-resource` | East US | GPT-4o inference |
| **Azure Cosmos DB** | `cosmoselderai3985` | West US 2 | Primary database, 14 containers |
| **Azure Communication Services** | `elder-ai-communication` | United States | SMS alerts, call automation |
| **Azure Key Vault** | `kvelderai9338` | East US | Secrets management |
| **Azure Application Insights** | `appielderai9338` | East US | Telemetry, monitoring |
| **Azure Active Directory** | Tenant `84c31ca0` | Global | Identity, `DefaultAzureCredential` |

### Cosmos DB Containers (14 total)

```
elderaidb/
├── users              (partition: /id)
├── sessions           (partition: /user_id)
├── medications        (partition: /user_id)
├── emergencies        (partition: /user_id)
├── emergency_contacts (partition: /user_id)
├── notifications      (partition: /user_id)
├── wellness           (partition: /user_id)
├── scam_reports       (partition: /user_id)
├── chat_sessions      (partition: /user_id)
├── chat_messages      (partition: /session_id)
├── analytics_events   (partition: /user_id)
├── alerts             (partition: /user_id)
├── audit_logs         (partition: /emergency_id)
└── threat_intel       (partition: /type)
```

---

## 🤖 Agent System

### Supervisor Agent (Orchestrator)

The Supervisor Agent is the brain of Elder AI Guardian. Built on **Semantic Kernel** and implementing the **Microsoft Agent Framework A2A protocol**, it:

1. **Classifies intent** from every user message
2. **Routes to the appropriate specialist agent**
3. **Coordinates multi-agent scenarios** (e.g., scam detected → alert family + log to DB simultaneously)
4. **Preserves context** across agent handoffs
5. **Escalates to emergency** when any agent detects critical risk

```python
# Intent routing logic
intent_routing = {
    "emergency":   ["help", "sos", "fall", "hurt", "pain", "chest"],
    "scam":        ["suspicious", "email", "call", "prize", "won"],
    "medication":  ["pill", "medicine", "tablet", "reminder", "dose"],
    "wellness":    ["feeling", "mood", "sleep", "appetite", "pain"],
    "family":      ["family", "contact", "notify", "call"],
    "general":     ["*"]  # catch-all
}
```

### Emergency Agent

- **Severity classification**: LOW / MEDIUM / HIGH / CRITICAL
- **Location handling**: GPS coordinates + reverse geocoding
- **Contact notification**: Automatic alert to all emergency contacts via ACS SMS
- **Fall detection**: Sensor data analysis for automatic fall detection
- **Cosmos DB write**: Every emergency persisted with full context

### Scam Detection Agent

- **Dual-mode analysis**: GPT-4o reasoning (primary) + rule-based (5s timeout fallback)
- **Threat profiling**: 8 scam types, urgency scoring, emotional manipulation detection
- **Community database**: MCP-powered phone number verification
- **Risk scoring**: 0-100 score → LOW/MEDIUM/HIGH/CRITICAL classification
- **Family escalation**: HIGH/CRITICAL automatically notifies family

### Medication Agent

- **NLP extraction**: Describe medication in plain English → AI extracts structured data
- **Schedule management**: Multiple daily doses with smart time scheduling
- **Adherence tracking**: Taken/missed logging → 7-day statistics
- **Refill management**: Proactive alerts 7 days before depletion
- **Cosmos DB**: Full medication history with timestamps

### Wellness Agent

- **Multi-dimensional tracking**: Mood (1-10), pain (1-10), sleep hours, appetite
- **Trend analysis**: GPT-4o identifies patterns → actionable insights
- **Report generation**: Weekly wellness summaries for family
- **Tip generation**: Personalized wellness advice
- **Alert thresholds**: Deteriorating trends trigger family notification

### Family Notification Agent

- **Multi-channel**: SMS via ACS, WebSocket push, in-app notification
- **Templated messages**: Context-aware notification text per event type
- **Severity gating**: Configurable per-contact alert thresholds
- **Cosmos DB logging**: Full notification history

### DevOps Agent

- **Continuous monitoring**: CPU, memory, disk, error rates — every 60 seconds
- **Autonomous healing**: Detects and fixes issues without human intervention
- **Metrics exposure**: `/api/metrics` endpoint for external monitoring
- **Application Insights**: All telemetry streamed to Azure Monitor
- **Self-healing actions**: Cache reinit, MCP context cleanup, service restart

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Azure subscription with services configured (see [Azure Services](#azure-services))
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/elder-ai-guardian.git
cd elder-ai-guardian
```

### 2. Backend Setup

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration

Create a `.env` file in the project root:

```env
# Application
APP_NAME="Elder AI Guardian"
APP_ENV="development"
SECRET_KEY="your-super-secret-key-minimum-32-chars"
PORT=8000

# Azure OpenAI (required)
AZURE_OPENAI_ENDPOINT="https://YOUR-RESOURCE.services.ai.azure.com/"
AZURE_OPENAI_KEY="your-azure-openai-key"
AZURE_OPENAI_DEPLOYMENT="gpt-4o"
AZURE_OPENAI_API_VERSION="2025-01-01-preview"

# Azure Cosmos DB (required)
COSMOS_DB_CONNECTION="AccountEndpoint=https://YOUR-COSMOS.documents.azure.com:443/;AccountKey=YOUR-KEY;"
COSMOS_DB_DATABASE="elderaidb"

# Azure Communication Services (optional — enables real SMS)
AZURE_COMMS_CONNECTION_STRING="endpoint=https://YOUR-ACS.communication.azure.com/;accesskey=YOUR-KEY"
AZURE_COMMS_PHONE="+1XXXXXXXXXX"

# Azure Application Insights (optional — enables monitoring)
APPINSIGHTS_INSTRUMENTATION_KEY="your-instrumentation-key"

# Azure Key Vault (optional)
AZURE_KEYVAULT_URL="https://YOUR-VAULT.vault.azure.net"

# CORS
CORS_ORIGINS="http://localhost:3000,http://localhost:5173"
WORKERS=1
```

### 4. Start the Backend

```bash
python run.py
```

You should see:
```
════════════════════════════════════════════════════════════════
    ELDER AI GUARDIAN - MICROSOFT FOUNDRY EDITION
    Hero Technologies: Foundry, MCP, Agent Framework, Agentic DevOps
════════════════════════════════════════════════════════════════

✅ Microsoft Agent Framework initialized with Azure OpenAI
✅ Foundry Agent initialized with 5 models
✅ SUPERVISOR AGENT INITIALIZED SUCCESSFULLY!
   Total agents: 6 (emergency, scam, medication, family, wellness, general)
✅ COSMOS DB INITIALIZED — 14 containers
✅ ELDER AI GUARDIAN IS READY!

API Documentation: http://127.0.0.1:8000/api/docs
WebSocket: ws://127.0.0.1:8000/ws/{user_id}
```

### 5. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:3000` or `http://localhost:5173`

### 6. Create a Test User

```bash
# Using the API directly
curl -X POST http://127.0.0.1:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@elderai.com","password":"Test1234!","name":"Test Elder"}'
```

Or visit `http://localhost:3000/register` in the browser.

---

## 📡 API Reference

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/register` | Create new account |
| `POST` | `/api/auth/login` | Login, returns JWT token |
| `GET` | `/api/auth/me` | Get current user profile |

### Emergency

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/emergency/sos` | Trigger SOS emergency |
| `POST` | `/api/emergency/{id}/resolve` | Mark emergency resolved |
| `GET` | `/api/emergency/history/{user_id}` | Get emergency history |

**SOS Request Body:**
```json
{
  "userId": "user-uuid",
  "message": "I've fallen and can't get up",
  "emergencyType": "medical",
  "location": {
    "latitude": 10.8505,
    "longitude": 76.2711,
    "accuracy": 5.0
  }
}
```

### Scam Detection

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/scam/analyze` | Analyze message for scams |
| `POST` | `/api/scam/url` | Check URL for phishing |
| `GET` | `/api/scam/stats/{user_id}` | Get scam statistics |

**Analyze Request Body:**
```json
{
  "message": "Congratulations! You have won $1,000,000...",
  "user_id": "user-uuid",
  "url": "https://claim-prize.suspicious.tk"
}
```

**Sample Response:**
```json
{
  "is_scam": true,
  "risk_score": 87.5,
  "risk_level": "CRITICAL",
  "confidence": 0.94,
  "scam_type": "lottery",
  "detection_methods": {
    "keyword_analysis": true,
    "ai_reasoning": true,
    "threat_profiling": true
  },
  "recommendations": [
    "🚨 DO NOT RESPOND to this message",
    "🚨 DO NOT CLICK any links",
    "📞 Call your family member immediately"
  ]
}
```

### Chat

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/chat/` | Send message to AI |
| `GET` | `/api/chat/history/{session_id}` | Get chat history |

### Dashboard

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/dashboard/` | Get dashboard metrics |
| `GET` | `/api/metrics` | System health metrics |
| `GET` | `/api/health` | Health check |

### WebSocket

Connect to `ws://localhost:8000/ws/{user_id}`

**Message types:**

```javascript
// Send ping
{ "type": "ping" }

// Send chat message
{ "type": "chat", "content": "Help me check this email", "sessionId": "session-id" }

// Trigger emergency
{ "type": "emergency", "message": "I've fallen", "location": {...} }

// Get MCP tools
{ "type": "mcp_tools" }

// Subscribe to live alerts
{ "type": "subscribe_alerts", "user_id": "elder-id" }

// Test alert
{ "type": "test_alert", "severity": "HIGH", "title": "Test" }
```

**Received message types:**
- `connected` — connection confirmed with hero technologies status
- `pong` — ping response
- `chat_response` — AI agent response
- `mcp_tools` — list of 9 available MCP tools
- `metrics` — system metrics update
- `live_alert` — real-time alert (emergency, scam, medication)
- `emergency_response` — emergency processing result

---

## 📁 Project Structure

```
elder-ai-guardian/
├── app/
│   ├── main.py                          # FastAPI app, WebSocket, lifespan
│   ├── agents/
│   │   ├── emergency/
│   │   │   └── emergency_agent.py       # SOS, fall detection, GPS
│   │   ├── scam_detection/
│   │   │   ├── scam_agent.py            # GPT-4o threat profiling
│   │   │   └── ml_models/
│   │   │       └── phishing_classifier.py
│   │   ├── medication/
│   │   │   ├── medication_agent.py      # Reminders, adherence tracking
│   │   │   └── function_calling.py
│   │   ├── wellness/
│   │   │   └── wellness_agent.py        # Health monitoring
│   │   ├── family_notification/
│   │   │   └── notification_agent.py    # SMS, alerts
│   │   ├── foundry/
│   │   │   ├── foundry_agent.py         # Azure Foundry integration
│   │   │   ├── model_router.py          # 5-strategy model routing
│   │   │   └── enhanced_model_router.py
│   │   ├── microsoft_framework/
│   │   │   └── supervisor_agent.py      # Microsoft Agent Framework
│   │   └── orchestrator/
│   │       ├── supervisor_agent.py      # Main orchestrator
│   │       ├── intent_agent.py          # Intent classification
│   │       └── intent_classifier.py
│   ├── api/
│   │   └── routes/
│   │       ├── auth.py                  # JWT authentication
│   │       ├── chat.py                  # Chat endpoint
│   │       ├── dashboard.py             # Dashboard metrics
│   │       ├── emergency.py             # SOS routes
│   │       ├── scam.py                  # Scam analysis
│   │       ├── medication.py            # Medication management
│   │       ├── wellness.py              # Wellness tracking
│   │       ├── family.py                # Family portal
│   │       ├── websocket.py             # WebSocket helpers
│   │       ├── hero.py                  # Hero tech showcase
│   │       ├── admin.py                 # Admin dashboard
│   │       ├── analytics.py             # Analytics
│   │       ├── azure.py                 # Azure service proxies
│   │       ├── devops.py                # DevOps endpoints
│   │       ├── health.py                # Health check
│   │       ├── notification.py          # Notification management
│   │       └── users.py                 # User management
│   ├── services/
│   │   ├── azure/
│   │   │   ├── communication_service.py # ACS SMS + calls
│   │   │   ├── mcp_service.py           # MCP tools
│   │   │   ├── foundry_service.py       # Foundry project
│   │   │   ├── search_service.py        # Azure Search
│   │   │   ├── storage_service.py       # Blob storage
│   │   │   └── event_service.py         # Event Grid + Service Bus
│   │   ├── database/
│   │   │   ├── cosmos_service.py        # Cosmos DB (14 containers)
│   │   │   └── base.py
│   │   ├── auth/
│   │   │   └── auth_service.py          # JWT + Cosmos auth
│   │   ├── cache/
│   │   │   └── cache_service.py         # Redis cache
│   │   ├── devops/
│   │   │   ├── devops_agent.py          # Autonomous DevOps
│   │   │   └── self_healing_agent.py    # Self-healing logic
│   │   ├── metrics/
│   │   │   └── metrics_service.py       # App Insights telemetry
│   │   ├── mcp/
│   │   │   └── mcp_server.py            # MCP server implementation
│   │   └── notification/
│   │       └── notification_service.py
│   ├── core/
│   │   ├── config.py                    # Settings management
│   │   ├── logging.py                   # Structured logging
│   │   ├── middleware.py                # Auth, rate limit, logging
│   │   ├── exceptions.py                # Global exception handlers
│   │   └── dependencies.py              # FastAPI dependencies
│   └── models/
│       └── schemas.py                   # Pydantic models
├── frontend/
│   ├── src/
│   │   ├── App.jsx                      # Root component + routing
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx            # Main dashboard
│   │   │   ├── Chat.jsx                 # AI chat interface
│   │   │   ├── Emergency.jsx            # SOS + emergency management
│   │   │   ├── ScamDetection.jsx        # Scam analysis UI
│   │   │   ├── Medication.jsx           # Medication management
│   │   │   ├── Wellness.jsx             # Wellness tracking
│   │   │   ├── FamilyPortal.jsx         # Family dashboard
│   │   │   ├── HeroShowcase.jsx         # Tech showcase
│   │   │   ├── Login.jsx                # Authentication
│   │   │   ├── Register.jsx             # Registration
│   │   │   └── Settings.jsx             # User settings
│   │   ├── contexts/
│   │   │   ├── WebSocketContext.jsx     # WebSocket state management
│   │   │   └── AzureContext.jsx         # Azure services context
│   │   ├── stores/
│   │   │   ├── authStore.js             # Zustand auth store
│   │   │   └── emergencyStore.js        # Emergency state
│   │   ├── services/
│   │   │   └── api.js                   # Axios instance + interceptors
│   │   └── components/
│   │       ├── Layout/Layout.jsx        # App shell
│   │       ├── PanicMode.jsx            # Full-screen emergency
│   │       └── ProtectedRoute.jsx       # Auth guard
│   ├── package.json
│   └── vite.config.js
├── infrastructure/
│   └── main.bicep                       # Azure infrastructure as code
├── scripts/
│   ├── deploy.ps1                       # Deployment script
│   ├── devops_agent.py                  # Standalone DevOps runner
│   └── seed_threats.py                  # Seed scam threat database
├── requirements.txt                     # Python dependencies
├── run.py                               # Application entry point
└── docker-compose.yml                   # Docker deployment
```

---

## 🎬 Demo

### Demo Video
[📺 Watch the 2-minute demo](https://youtube.com/YOUR_VIDEO_LINK)

### Key Demo Scenarios

**Scenario 1: Scam Detection**
1. Navigate to **Scam Detection**
2. Paste: `"Congratulations! You have won $1,000,000. Click here to claim your prize now!"`
3. Click **Analyze**
4. Watch GPT-4o return **CRITICAL RISK** with full threat profile in under 5 seconds

**Scenario 2: Emergency SOS**
1. Navigate to **Emergency**
2. Click **Medical Emergency**
3. Confirm SOS
4. Watch: GPS captured → Cosmos DB written → Family notified → Step tracker advances

**Scenario 3: AI Chat**
1. Navigate to **Chat**
2. Type: `"I think I'm having a heart attack"`
3. Watch: Supervisor → Emergency Agent → CRITICAL response with 911 instructions

**Scenario 4: Real-time Dashboard**
1. Navigate to **Dashboard**
2. Observe: WebSocket **🟢 Live** badge
3. All hero tech badges lit: Foundry ✅ MCP ✅ Agent Framework ✅ DevOps ✅ Cosmos DB ✅

### Live API Testing

Visit `http://127.0.0.1:8000/api/docs` for interactive Swagger UI with all endpoints.

---

## 🔒 Security Notes

> ⚠️ **Important**: The `.env` file shown in this repository contains example values. **Never commit real credentials to GitHub.** All Azure service keys should be stored in Azure Key Vault in production.

For production deployment:
1. Use `DefaultAzureCredential` with Managed Identity
2. Store all secrets in Azure Key Vault (`kvelderai9338`)
3. Enable Azure AD authentication
4. Configure proper CORS origins
5. Set `APP_ENV=production`

---

## 📊 Performance Metrics

| Metric | Value |
|--------|-------|
| API response time | < 200ms (non-AI endpoints) |
| GPT-4o response time | 1-3 seconds |
| Scam detection (rule-based fallback) | < 100ms |
| WebSocket connection time | < 50ms |
| Cosmos DB write | < 200ms |
| System startup time | ~15 seconds |
| Active WebSocket connections | Unlimited |
| Cosmos DB containers | 14 |
| MCP tools available | 9 |
| Specialized agents | 6 |

---

## 🌐 Deployment

### Docker

```bash
docker-compose up --build
```

### Azure Container Apps (Production)

```bash
# Deploy infrastructure
az deployment group create \
  --resource-group elderai-rg \
  --template-file infrastructure/main.bicep

# Deploy application
./scripts/deploy.ps1
```

---

## 🏅 Hackathon Submission

**Event**: Microsoft AI Dev Days Hackathon 2026  
**Category**: Best Multi-Agent System, Best Azure Integration  
**Built by**: Solo developer  
**Time**: 48 hours  
**Azure Subscription**: `4ca5d404-5a2a-4bfe-a751-8fbe5cdffe59`  

### Why This Wins

1. **All 4 hero technologies** implemented — not just one or two
2. **Real Azure services** — live Cosmos DB, real GPT-4o, real ACS with actual phone number
3. **Social impact** — addresses a genuine, urgent global problem
4. **Production-ready architecture** — not a toy demo
5. **Solo build** — demonstrates exceptional technical depth
6. **Complete end-to-end** — from UI to database, everything works

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

**Built with ❤️ for the elders who deserve better**

*Microsoft AI Dev Days Hackathon 2026*

[![Azure](https://img.shields.io/badge/Powered_by-Microsoft_Azure-0078D4?style=flat-square&logo=microsoft-azure)](https://azure.microsoft.com)
[![GPT-4o](https://img.shields.io/badge/AI-GPT--4o-412991?style=flat-square)](https://openai.com)
[![Semantic Kernel](https://img.shields.io/badge/Agents-Semantic_Kernel-5C2D91?style=flat-square&logo=microsoft)](https://aka.ms/semantic-kernel)

</div>
