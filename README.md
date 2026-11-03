# TriageForge

Autonomous AI support ticket triage platform with a verifiable LangGraph execution agent, customer sentiment detection, multi-tone response adaptation, and a high-contrast Brutalist operator dashboard.

---

## Table of Contents

- [Overview](#overview)
- [How It Works](#how-it-works)
- [System Architecture](#system-architecture)
- [Backend Deep Dive](#backend-deep-dive)
- [Frontend Deep Dive & Design System](#frontend-deep-dive--design-system)
- [Seed Ticket Scenarios](#seed-ticket-scenarios)
- [Step-by-Step Setup Guide](#step-by-step-setup-guide)
  - [Prerequisites](#prerequisites)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
- [Environment Variables Reference](#environment-variables-reference)
- [Testing & Quality Assurance](#testing--quality-assurance)
- [Security & Prompt Injection Defenses](#security--prompt-injection-defenses)

---

## Overview

TriageForge automates the operational triage of customer support tickets while maintaining strict traceability and factual grounding. When a support request arrives, an autonomous LangGraph agent inspects the message, dynamically decides whether external tools (such as order tracking or account tier verification) are required, executes validated tool calls, and generates a polite, fact-checked response draft under 120 words.

Every decision step, tool parameter, raw output payload, and reasoning rationale is captured and streamed in real time to the operator dashboard via Server-Sent Events (SSE).

---

## How It Works

The platform operates through a coordinated six-stage lifecycle:

```
[Customer Ticket Ingestion]
           │
           ▼
[Stage 1: Ingestion & Thread-Safe Queue]
Initializes ticket record (Pending status) in memory store.
           │
           ▼
[Stage 2: LangGraph Cyclical Evaluation (agent_node)]
Model evaluates ticket content and metadata. Decides between calling a support tool or finalizing.
           │
      ┌────┴──────────────────────────┐
      ▼                               ▼
[Stage 3: Tool Execution]      [Stage 4: Synthesis & Policy]
Executes mock tools safely.    Validates facts, detects mood,
Re-enters agent_node loop.     generates tone variants.
      │                               │
      └───────────────────────────────┘
                      │
                      ▼
[Stage 5: Live SSE Telemetry Streaming]
Emits granular trace events to the Next.js client over POST SSE stream.
                      │
                      ▼
[Stage 6: Operator Review & Action]
Displays verified draft, customer mood badge, 1-click tone switcher, and full trace blocks.
```

---

## System Architecture

```
TriageForge/
├── backend/
│   ├── app/
│   │   ├── agent/             # LangGraph state machine, output policy, prompts
│   │   │   ├── graph.py       # Compiled StateGraph workflow with conditional edges
│   │   │   ├── nodes.py       # agent_node, tool_node, finalize_node definitions
│   │   │   ├── output_policy.py # Fact grounding, mood detection, tone variant synthesis
│   │   │   ├── prompts.py     # System instructions and operational boundaries
│   │   │   └── state.py       # TypedDict state tracking messages and trace log
│   │   ├── api/routes/        # FastAPI endpoints (/tickets, /tickets/{id}/triage)
│   │   ├── core/              # Config, logging, seed data, in-memory rate limiters
│   │   ├── schemas/           # Pydantic v2 domain schemas (Ticket, TraceStep, TriageResult)
│   │   ├── services/          # TicketStore and triage streaming service coordinator
│   │   ├── tools/             # Mock external support tools with regex validation
│   │   └── main.py            # FastAPI entry point, CORS, lifespan, and exception handlers
│   └── tests/                 # Pytest async unit and integration suite
│
├── frontend/
│   ├── src/
│   │   ├── app/               # Next.js App Router (layout, globals.css, page.tsx)
│   │   ├── components/        # TicketDashboard, TicketDetail, TraceAccordion, OutputCard
│   │   ├── lib/               # Resilient fetch wrapper, constants, SSE event parser
│   │   └── types/             # Strict TypeScript models matching backend schemas
│   ├── package.json
│   ├── next.config.ts
│   └── tsconfig.json
│
├── .agent/                    # Autonomous agent engineering specifications
├── .docs/                     # Architectural documentation, checklists, business logic
└── README.md                  # Project documentation
```

---

## Backend Deep Dive

### 1. State Machine Implementation
The backend uses LangGraph to construct a cyclical decision graph rather than a brittle linear chain:
- **`agent_node`**: Binds tools to the language model. Inspects conversation history and determines if external data is needed.
- **`tool_node`**: Executes approved support tools. Enforces strict parameter matching against ticket metadata to reject injected arguments.
- **`finalize_node`**: Invokes structured schema generation, producing validated `draft`, `tag`, and `reasoning` fields.
- **Conditional Routing**: The router examines tool calls on the latest message. If tools exist and call budget (< 3) permits, routes to `tool_node`; otherwise proceeds to `finalize_node`.

### 2. Output Policy & Grounding
To prevent hallucinations, `apply_business_rules()` enforces deterministic constraints:
- Order status inquiries must strictly cite the order ID, shipment status, and delivery ETA returned by `get_order_status`.
- Subscription upgrade inquiries must confirm current tier eligibility from `get_user_tier` and assign the `Escalate to Sales` tag without making unverified promises.
- Word count is enforced under 120 words via Pydantic validators.

### 3. Customer Mood Detection & Tone Switcher Engine
During finalization, the output engine analyzes the customer's text markers:
- **Frustrated**: Detected when keywords indicate delivery delays or distress. Defaults to an Empathetic response tone.
- **Inquisitive**: Detected when keywords relate to plan upgrades or team features. Defaults to a Professional response tone.
- **Neutral**: Detected for standard technical how-to inquiries. Defaults to a Concise response tone.
- **Pre-computed Variants**: Generates factual adaptations across all three tones (`Empathetic`, `Concise`, `Professional`) so operators can switch styles instantly in the UI with zero latency.

### 4. API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Service uptime and health verification. |
| `GET` | `/tickets` | Retrieves full queue of support tickets. |
| `GET` | `/tickets/{ticket_id}` | Retrieves a single ticket by ID (returns 404 if missing). |
| `POST` | `/tickets/{ticket_id}/triage` | Executes synchronous agent triage and returns JSON payload. |
| `POST` | `/tickets/{ticket_id}/triage/stream` | Streams live trace steps and final result via Server-Sent Events. |

---

## Frontend Deep Dive & Design System

### 1. Brutalist Aesthetic
TriageForge implements an authentic industrial Brutalist design system optimized for operational clarity:
- **Canvas Palette**: Background `#FFF8E7` (warm paper), Surface `#FFFFFF`, High-contrast borders `#000000`.
- **Status Accents**: Pending `#FFE600` (Yellow), Processing `#4D79FF` (Blue), Resolved / Auto-Resolve `#3DDC84` (Green), Escalate to Sales `#FF6EC7` (Pink).
- **Zero Border Radius**: All buttons, cards, tags, and inputs enforce `border-radius: 0 !important`.
- **Refined Directional Shadows**: Softened, blurred offset shadows (`2px 4px 10px rgba(0, 0, 0, 0.14)`) providing depth without visual clutter.

### 2. Typographic Modular Scale
Typography strictly utilizes **Space Mono** (`var(--font-space-mono)`) across all elements with a deliberate modular scale:
- Hero Headings: `clamp(28px, 4vw, 36px)`, weight 700.
- Section & Panel Headings: `17px - 18px`, uppercase bold.
- Primary Customer Message & Draft: `16px`, line-height 1.8.
- Code & Data Payloads: `14px`, high-contrast terminal monospace.
- Controls & Buttons: `13px - 14px`, uppercase bold.
- Metadata & Badges: `11px - 12px`, letter-spacing 0.1em.
- Accessibility: No text rendered below 11px.

### 3. Handcrafted Loaders & Vector Iconography
- All generic circular spinning CSS rings have been eliminated.
- **Brutalist Stepper**: Three alternating micro-blocks (`.brutalist-stepper-sm`) for active button states.
- **Brutalist Activity Meter**: Four-cell stepped progress indicator (`.brutalist-meter-md`) for panels.
- **Industrial LED Dot**: Square pulsing green beacon (`.live-pulse-dot`) indicating active execution threads.
- **Vector Icons**: Custom 2.5px stroke SVG icons (`IconAlert`, `IconSearch`, `IconMessage`, `IconHeart`, `IconZap`, `IconBriefcase`, `IconCopy`, `IconCheck`) with zero emojis.

---

## Seed Ticket Scenarios

| Ticket ID | Scenario | Expected Agent Behavior | Final Resolution Tag |
|---|---|---|---|
| `TCK-001` | Delayed shipment inquiry for order `ORD-9012`. | Calls `get_order_status(order_id="ORD-9012")`. Identifies package is in transit with tomorrow ETA. | `Auto-Resolve` |
| `TCK-002` | Request to upgrade team from Free to Enterprise. | Calls `get_user_tier(user_id="USR-4411")`. Confirms eligibility, provides upgrade information. | `Escalate to Sales` |
| `TCK-003` | General how-to inquiry on exporting reports to CSV. | Recognizes self-service documentation query. Makes zero tool calls and provides direct guidance. | `Auto-Resolve` |

---

## Step-by-Step Setup Guide

### Prerequisites
- Python 3.11, 3.12, or 3.13
- Node.js 18.18+ or 20+
- Git

---

### Backend Setup

1. **Navigate to the backend directory**:
   ```bash
   cd d:\TriageForge\backend
   ```

2. **Create and activate a virtual environment**:
   - On Windows:
     ```powershell
     python -m venv venv
     .\venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   copy .env.example .env
   ```
   Open `backend/.env` and insert your API key:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   GROQ_MODEL=openai/gpt-oss-20b
   LLM_FALLBACK_MODEL=openai/gpt-oss-120b
   CORS_ORIGINS=http://localhost:3000
   MAX_TOOL_CALLS=3
   LLM_TIMEOUT_SECONDS=30
   LLM_REQUESTS_PER_MINUTE=60
   TEST_CONCURRENCY=2
   LLM_MAX_RETRIES=1
   TRIAGE_REQUESTS_PER_MINUTE=10
   ```

5. **Start the backend server**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   Verify by visiting `http://localhost:8000/health` (returns `{"status":"ok"}`) and OpenAPI docs at `http://localhost:8000/docs`.

---

### Frontend Setup

1. **Navigate to the frontend directory**:
   ```bash
   cd d:\TriageForge\frontend
   ```

2. **Install Node packages**:
   ```bash
   npm install
   ```

3. **Set up local environment variables**:
   ```bash
   copy .env.example .env.local
   ```
   Ensure `frontend/.env.local` contains:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

4. **Verify TypeScript compilation**:
   ```bash
   npm run typecheck
   ```

5. **Start the development server**:
   ```bash
   npm run dev
   ```
   Open `http://localhost:3000` in your browser.

6. **Build for production**:
   ```bash
   npm run build
   ```

---

## Environment Variables Reference

### Backend (`backend/.env`)

| Variable | Type | Default | Description |
|---|---|---|---|
| `GROQ_API_KEY` | String | Required | API key for the primary LLM provider. |
| `GROQ_MODEL` | String | `openai/gpt-oss-20b` | Primary chat completion model for triage. |
| `LLM_FALLBACK_MODEL` | String | `openai/gpt-oss-120b` | Secondary model invoked if primary encounters rate limits. |
| `CORS_ORIGINS` | String | `http://localhost:3000` | Comma-delimited list of allowed browser origins. |
| `MAX_TOOL_CALLS` | Integer | `3` | Maximum tool execution turns allowed per ticket run. |
| `LLM_TIMEOUT_SECONDS` | Integer | `30` | Timeout threshold for individual LLM network requests. |
| `LLM_REQUESTS_PER_MINUTE` | Integer | `60` | In-memory token bucket rate limit for outgoing model requests. |
| `TRIAGE_REQUESTS_PER_MINUTE` | Integer | `10` | IP-based rate limit for incoming triage API requests. |
| `TEST_CONCURRENCY` | Integer | `2` | Parallel execution bound for integration test batches. |

### Frontend (`frontend/.env.local`)

| Variable | Type | Default | Description |
|---|---|---|---|
| `NEXT_PUBLIC_API_URL` | String | `http://localhost:8000` | Base HTTP URL pointing to the active FastAPI backend. |

---

## Testing & Quality Assurance

### Backend Test Execution
Run the automated Pytest test suite covering mock tools, in-memory store consistency, LangGraph security constraints, and output policy grounding:

```bash
cd backend
python -m pytest tests/test_output_policy.py tests/test_store.py tests/test_tools.py -v
```

### Frontend Typechecking & Compilation
Run static TypeScript analysis and the Next.js production build:

```bash
cd frontend
npm run typecheck
npm run build
```

---

## Security & Prompt Injection Defenses

TriageForge incorporates active multi-layer security protections:
1. **Parameter Isolation**: The agent cannot supply arbitrary parameters to tools. For instance, `get_order_status` requires an `order_id` that strictly matches the ticket record regex (`^ORD-\d{4}$`).
2. **Execution Turn Limits**: A strict limit of 3 tool calls prevents denial-of-service loops or recursive prompt injection exploitation.
3. **HTML Sanitization**: All content rendered on the frontend is escaped via React DOM nodes; `dangerouslySetInnerHTML` is prohibited.
4. **Resilient Unmount Lifecycle**: The frontend client uses mounted ref guards preventing console abort errors during development fast-refresh or browser extension inspection.
