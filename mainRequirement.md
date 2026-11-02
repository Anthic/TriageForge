PROJECT: SUPPORTDESK AGENT
Target Role: Software Developer / Full-Stack Engineer
Submission Deadline: End of 03-Nov-2026
Primary Deliverables: Public GitHub Repo (Frontend + Backend), README, and trace log UI
Allowed AI Tools: Any available free version
1. Project Overview & Context
Welcome! As part of our technical evaluation, you are tasked with building a working prototype of
SupportAgent Desk, an AI-powered customer support triage application. The goal of this assignment is
to evaluate your full-stack web engineering fundamentals (UI state management, API routes, and clean
code structure) alongside practical function calling and execution trace observability using an LLM of your
choice.
Rather than building a simple chat prompt, your backend service will host an Autonomous Triage Agent.
The agent must evaluate support tickets, determine if missing context requires external tool execution,
invoke mock backend helper functions, and output structured resolutions while displaying an execution
trace log to the frontend dashboard.
2. System Architecture & Workflow
Frontend Dashboard UI ---> 1. User clicks 'Run AI Triage Agent'
Backend Agent API ---> 2. Evaluates ticket text & selects required tool schema
Mock Tool Execution ---> 3. Runs get_order_status(order_id) OR get_user_tier(user_id)
Agent Synthesis ---> 4. Returns final customer draft + action tag + trace log
3. Seed Data Specification
Your backend service must be initialized with the following 3 pre-seeded customer support tickets:
Ticket ID Customer &
Order ID

Ticket Description Expected Agent Behavior

TCK-001 User: USR-101
Order: ORD-9012

"Where is my package #ORD-
9012? It was supposed to

arrive yesterday."

Calls get_order_status -> Detects
status -> Drafts ETA response ->
Tags [Auto-Resolve]

TCK-002 User: USR-204
Order: None

"Can you upgrade my account
to Enterprise tier?"

Calls get_user_tier -> Checks tier
-> Drafts upgrade instructions ->
Tags [Escalate to Sales]

TCK-003 User: USR-309
Order: None

"How do I update my profile
picture?"

Recognizes no tool call is required
-> Responds directly -> Tags
[Auto-Resolve]

2

4. Technical Requirements
4.1 Frontend Dashboard
 Ticket List & Details: Display a list of pre-seeded tickets showing status badges (Pending,
Processing, Resolved). Clicking a ticket reveals its full metadata and message text.
 Action Trigger: Provide a prominent button labeled 'Run AI Triage Agent' on the detail view.
 UI Loading State: Visually indicate processing while the agent executes (disable action buttons, show
spinner/loading state).
 Output Card: Render the completed agent result featuring a Customer Response Draft and a
Resolution Tag Badge ([Auto-Resolve] or [Escalate to Sales]).
 Execution Trace UI: Include an expandable component titled 'Agent Execution Trace' displaying the
step-by-step audit log (e.g., Tool Called -> Parameters -> Raw Output -> Reasoning).
4.2 Backend Service & Mock Tools
 LLM Integration: Connect your backend to a real LLM API (OpenAI, Anthropic, Google AI Studio
Gemini Free Tier, or Ollama for local open-source models).
 Mock Function Implementations:
• get_order_status(order_id: string): Returns { order_id, status: 'In Transit', est_delivery:
'Tomorrow' }
• get_user_tier(user_id: string): Returns { user_id, current_tier: 'Free', eligible_for_upgrade: true }
 Agentic Tool Invocations: Define tool JSON/Pydantic schemas so the LLM dynamically decides
when to trigger these mock tools based on the ticket context.
 Error Handling: Ensure tool failures or missing parameters are handled gracefully without backend
crashes.
5. Submission Deliverables
Please submit your completed assignment with the following:
 GitHub Repository: Link to a public GitHub repository with a clean commit history.
 README.md: Includes simple setup instructions (e.g., `npm run dev`), environment variable notes
(`.env.example`).
 Environment Variables: An `.env.example` file specifying key names (e.g., `GEMINI_API_KEY`,
`OPENAI_API_KEY`, or `OLLAMA_HOST`).