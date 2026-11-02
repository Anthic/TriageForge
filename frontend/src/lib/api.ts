import type { ApiErrorPayload, Ticket, TriageResponse, TraceStep } from "@/types";

const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

export class ApiRequestError extends Error {
  readonly status: number;
  readonly code: string;
  readonly trace: TraceStep[];

  constructor(message: string, status: number, code: string, trace: TraceStep[] = []) {
    super(message);
    this.name = "ApiRequestError";
    this.status = status;
    this.code = code;
    this.trace = trace;
  }
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, { ...init, cache: "no-store" });
  } catch (error) {
    if (error instanceof Error && error.name === "AbortError") throw error;
    throw new ApiRequestError("Could not connect to the ticket service.", 0, "NETWORK_ERROR");
  }

  if (!response.ok) {
    const payload = (await response.json().catch(() => ({}))) as ApiErrorPayload;
    throw new ApiRequestError(
      payload.error?.message ?? "The request could not be completed.",
      response.status,
      payload.error?.code ?? "API_ERROR",
      payload.trace ?? [],
    );
  }
  return (await response.json()) as T;
}

export async function getTickets(signal?: AbortSignal): Promise<Ticket[]> {
  return requestJson<Ticket[]>("/tickets", { signal });
}

export async function runTicketTriage(ticketId: string): Promise<TriageResponse> {
  return requestJson<TriageResponse>(`/tickets/${encodeURIComponent(ticketId)}/triage`, {
    method: "POST",
    headers: { Accept: "application/json" },
  });
}
