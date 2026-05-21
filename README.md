# HCP CRM - Healthcare Professional Interaction Logging Module

### launch

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # Add GROQ_API_KEY, DATABASE_URL
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm start   # runs on http://localhost:3000
```

### Database
```bash
# With Docker
docker run --name hcp-db -e POSTGRES_PASSWORD=secret -e POSTGRES_DB=hcp_crm -p 5432:5432 -d postgres:15
cd backend
alembic upgrade head
```

---

## LangGraph Agent 

The LangGraph agent acts as an **intelligent orchestrator** for HCP interaction management. Instead of rigid API endpoints, it reasons over the sales rep's intent , selects the right tool, calls it, and returns a structured result.

### Why LangGraph?
- **Stateful conversations**: maintains multi-turn dialogue context across a session
- **Tool routing**: the LLM decides which tool to call based on natural language intent
- **Fallback logic**: if a tool fails, the graph can retry or ask for clarification
- **Auditability**: every node transition is logged for compliance

### The 5 Agent Tools

1  `log_interaction`  Capture raw notes - extract entities - summarize - persist 
2  `edit_interaction`  Fetch existing record - apply partial update - re-summarize 
3 `get_hcp_profile` Pull HCP details
4  `schedule_followup`  Parse date intent - create calendar follow-up task 
5  `search_interactions`  Semantic + keyword search over interaction history 

---

## Project Structure

```
hcp-crm/
├── README.md
├── backend/
│   ├── requirements.txt
│   ├── .env.example
│   |── app/
│       ├── main.py              # FastAPI app entry point
        |__rate_limit.py
│       ├── config.py            # Settings via pydantic-settings
│       ├── database.py          # SQLAlchemy async engine
│       ├── models/
│       │   ├── hcp.py           # HCP ORM model
│       │   ├── interaction.py   # Interaction ORM model
│       │   └── follow_up.py     # FollowUp ORM model
│       ├── schemas/
│       │   ├── hcp.py           # Pydantic request/response schemas
│       │   └── interaction.py
│       ├── routes/
│       │   ├── interactions.py  # REST endpoints
│       │   ├── hcps.py
│       │   └── chat.py          # Streaming chat endpoint
│       ├── agents/
│       │   ├── graph.py         # LangGraph state machine definition
│       │   └── state.py         # AgentState TypedDict
│       └── tools/
│           ├── log_interaction.py
│           ├── edit_interaction.py
│           ├── get_hcp_profile.py
│           ├── schedule_followup.py
│           └── search_interactions.py
└── frontend/
    ├── package.json
    └── src/
        ├── index.js
        ├── App.jsx
        ├── store/
        │   ├── index.js         # Redux store
        │   ├── interactionSlice.js
        │   └── chatSlice.js
        ├── api/
        │   └── client.js        # Axios instance + endpoints
        ├── components/
        │   ├── LogInteractionScreen.jsx   # Main screen
        │   ├── StructuredForm.jsx         # Form mode
        │   ├── ChatInterface.jsx          # Chat mode
        │   ├── ModeToggle.jsx
        │   └── InteractionCard.jsx
        └── styles/
            └── global.css
```
