# Aurora Forester System Architecture

**Version:** 1.0.0
**Date:** December 3, 2025

---

## Overview

Aurora Forester is a multi-channel, persistent, RAG-enabled collaborative agentic system. This document defines the complete technical architecture.

---

## System Diagram

```
┌────────────────────────────────────────────────────────────────────────┐
│                        ACCESS CHANNELS                                  │
├──────────────┬──────────────┬──────────────┬──────────────┬────────────┤
│   Discord    │    Tablet    │     SMS      │   Webhook    │  Terminal  │
│     Bot      │    (PWA)     │   Gateway    │     API      │ (Claude)   │
└──────┬───────┴──────┬───────┴──────┬───────┴──────┬───────┴─────┬──────┘
       │              │              │              │             │
       └──────────────┴──────────────┼──────────────┴─────────────┘
                                     │
                            ┌────────▼────────┐
                            │   Message Bus   │
                            │   (Redis/NATS)  │
                            └────────┬────────┘
                                     │
                            ┌────────▼────────┐
                            │  Aurora Core    │
                            │   (LangGraph)   │
                            └────────┬────────┘
                                     │
       ┌─────────────────────────────┼─────────────────────────────┐
       │                             │                             │
┌──────▼──────┐              ┌───────▼───────┐              ┌──────▼──────┐
│  PostgreSQL │              │  Ollama LLM   │              │ HuggingFace │
│ + pgvector  │              │   (Local)     │              │   (Cloud)   │
└─────────────┘              └───────────────┘              └─────────────┘
```

---

## Database Architecture

### Schemas

| Schema | Purpose |
|--------|---------|
| `aurora_core` | Conversations, messages, founder profile |
| `aurora_tasks` | Projects, todos, backlog |
| `aurora_learning` | Observations, patterns, limitations, feedback |
| `aurora_agents` | Spawned agents, workflows, executions |
| `aurora_credentials` | Encrypted API keys and tokens |
| `aurora_context` | RAG document library with embeddings |

### Key Tables

- **founder_profile**: Encrypted personal preferences and patterns
- **conversations**: Channel-agnostic conversation tracking
- **messages**: Individual messages with vector embeddings
- **tasks**: Todo items with priority and project association
- **patterns**: Learned behavioral patterns
- **workflows**: n8n, LangChain, LangGraph definitions

---

## Multi-Channel Access

### 1. Discord Bot (✅ Deployed)
- **Status**: Running in aurora-system namespace
- **Channel**: aurora-forester (private)
- **Security**: Role-based access, redirect non-founders to Otto

### 2. Tablet Interface (PWA)
- **Technology**: Progressive Web App
- **Features**:
  - Full conversation interface
  - Task management
  - Quick capture
  - Offline support
- **Auth**: Token-based, stored locally

### 3. SMS Gateway
- **Options**:
  - Twilio (paid, reliable)
  - Signal API (secure, complex)
  - Matrix bridge (self-hosted)
- **Flow**: SMS → n8n webhook → Aurora Core → Response → SMS

### 4. Webhook API
- **Endpoint**: `/api/aurora/message`
- **Auth**: API key + HMAC signature
- **Hosting**: n8n or custom FastAPI

### 5. Terminal Access (Claude Code)
- **Integration**: Direct invocation via commands
- **BMAD**: Can spawn BMAD agents
- **Output**: Responses in terminal

---

## LangGraph Architecture

Aurora Core is implemented as a LangGraph agent with stateful conversation management.

```python
# Aurora LangGraph Structure
graph = StateGraph(AuroraState)

# Nodes
graph.add_node("understand", understand_intent)
graph.add_node("retrieve", rag_retrieve)
graph.add_node("think", generate_response)
graph.add_node("act", execute_action)
graph.add_node("learn", update_patterns)

# Edges
graph.add_edge("understand", "retrieve")
graph.add_conditional_edges("retrieve", route_by_intent)
graph.add_edge("think", "act")
graph.add_edge("act", "learn")
graph.add_edge("learn", END)
```

### State Management

```python
class AuroraState(TypedDict):
    # Conversation
    messages: List[Message]
    channel: str
    session_id: str

    # Context
    founder_context: Dict
    relevant_docs: List[Document]
    active_tasks: List[Task]

    # Intent
    intent: str
    entities: List[Entity]

    # Response
    response: str
    actions_taken: List[Action]

    # Learning
    observations: List[Observation]
```

---

## HuggingFace Integration

### Access
- **Token**: Stored in aurora_credentials table (encrypted)
- **Models**: Listed and accessible via API

### Use Cases
1. **Embedding Models**: For RAG vector storage
2. **Specialized Models**: Sentiment, classification, etc.
3. **Fine-tuning**: Custom models for Aurora
4. **Model Discovery**: Aurora can search for models

### Implementation
```python
from huggingface_hub import HfApi

class AuroraHuggingFace:
    def __init__(self, token: str):
        self.api = HfApi(token=token)

    def search_models(self, query: str, task: str = None):
        """Search for models by query and optional task"""
        return self.api.list_models(search=query, filter=task)

    def get_embeddings(self, texts: List[str], model: str):
        """Generate embeddings using specified model"""
        # Implementation using inference API
        pass
```

---

## n8n Workflow Integration

### Webhook Triggers
- `/webhook/aurora/discord` - Discord events
- `/webhook/aurora/sms` - SMS incoming
- `/webhook/aurora/tablet` - Tablet app events
- `/webhook/aurora/scheduled` - Scheduled tasks

### Example Workflows
1. **Morning Brief**: Scheduled → Gather context → Generate summary → Send to Discord
2. **SMS Handler**: SMS → Parse → Aurora Core → Response → Send SMS
3. **Task Reminder**: Scheduled → Check due tasks → Generate reminder → Notify

---

## Agent Spawning

Aurora can create specialized agents for specific tasks.

### Agent Types
1. **Research Agents**: Deep dive into topics
2. **Workflow Agents**: Execute multi-step processes
3. **Monitor Agents**: Watch for conditions
4. **BMAD Agents**: Leverage BMAD capabilities

### Spawning Process
```python
async def spawn_agent(purpose: str, agent_type: str, config: dict):
    """Spawn a specialized agent for a task"""
    agent = SpawnedAgent(
        name=f"{agent_type}_{uuid4().hex[:8]}",
        purpose=purpose,
        agent_type=agent_type,
        configuration=config
    )
    await agent.save()

    # Execute based on type
    if agent_type == "research":
        return await run_research_agent(agent)
    elif agent_type == "workflow":
        return await run_workflow_agent(agent)
    # etc.
```

---

## Security Model

### Authentication
- **Discord**: Bot token + role verification
- **Tablet**: JWT tokens with refresh
- **SMS**: Phone number verification
- **Webhook**: API key + HMAC signature
- **Terminal**: Local only, implicit trust

### Data Protection
- Credentials encrypted with pgcrypto
- Sensitive founder profile fields encrypted
- Sector7 project marked as protected
- Private documents filtered from RAG

### Access Control
- Founder: Full access all channels
- Authorized users (Menley, Coby): Discord only
- Others: Redirected to Otto

---

## Deployment Architecture

### Kubernetes Namespaces
```
aurora-system/
├── aurora-bot (Discord bot) ✅
├── aurora-postgres (Database) ✅
├── aurora-api (Webhook/REST API)
├── aurora-worker (LangGraph processor)
└── aurora-tablet (PWA server)

otto-system/
├── otto-bot (Discord bot) ✅
└── otto-knowledge (ConfigMap) ✅
```

### Resource Requirements
| Component | CPU | Memory |
|-----------|-----|--------|
| aurora-bot | 100m-500m | 256Mi-512Mi |
| aurora-postgres | 100m-500m | 256Mi-512Mi |
| aurora-api | 100m-250m | 128Mi-256Mi |
| aurora-worker | 200m-1000m | 512Mi-1Gi |

---

## Integration Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      AURORA ECOSYSTEM                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │   Discord   │    │   Tablet    │    │    SMS      │         │
│  │     Bot     │    │    PWA      │    │   Gateway   │         │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘         │
│         │                  │                  │                 │
│         └──────────────────┼──────────────────┘                 │
│                            │                                    │
│                   ┌────────▼────────┐                          │
│                   │   Aurora Core   │                          │
│                   │   (LangGraph)   │                          │
│                   └────────┬────────┘                          │
│                            │                                    │
│         ┌──────────────────┼──────────────────┐                │
│         │                  │                  │                 │
│  ┌──────▼──────┐   ┌───────▼──────┐   ┌──────▼──────┐         │
│  │  PostgreSQL │   │    Ollama    │   │ HuggingFace │         │
│  │  + pgvector │   │    (LLM)     │   │   Models    │         │
│  └─────────────┘   └──────────────┘   └─────────────┘         │
│                                                                  │
│  ┌─────────────┐   ┌──────────────┐   ┌─────────────┐         │
│  │    n8n      │   │  Claude Code │   │    BMAD     │         │
│  │  Workflows  │   │   Terminal   │   │   Agents    │         │
│  └─────────────┘   └──────────────┘   └─────────────┘         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Next Steps

1. **Apply database schema** to aurora-postgres
2. **Implement LangGraph core** with state management
3. **Set up n8n webhooks** for multi-channel routing
4. **Create tablet PWA** with offline support
5. **Configure SMS gateway** (Twilio recommended)
6. **Add HuggingFace integration** for model access

---

*Architecture designed collaboratively by the BMAD Party-Mode team.*
