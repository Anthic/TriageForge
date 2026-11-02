export type TicketStatus = "Pending" | "Processing" | "Resolved";

export interface Ticket {
  id: string;
  user_id: string;
  order_id: string | null;
  text: string;
  status: TicketStatus;
  created_at: string;
}

export type ResolutionTag = "Auto-Resolve" | "Escalate to Sales";

export interface TriageResult {
  draft: string;
  tag: ResolutionTag;
  reasoning: string;
}

export interface TraceStep {
  step: number;
  node: string;
  type: "tool_call" | "tool_result" | "reasoning" | "final" | "error";
  tool?: string | null;
  parameters?: Record<string, unknown> | null;
  raw_output?: unknown;
  reasoning?: string | null;
  duration_ms: number;
  timestamp: string;
}

export interface TriageResponse {
  ticket: Ticket;
  result: TriageResult;
  trace: TraceStep[];
}

export interface ApiErrorPayload {
  error?: {
    code?: string;
    message?: string;
  };
  trace?: TraceStep[];
}
