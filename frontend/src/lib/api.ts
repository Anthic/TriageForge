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

export async function streamTicketTriage(
  ticketId: string,
  onTrace: (step: TraceStep) => void,
): Promise<TriageResponse> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/tickets/${encodeURIComponent(ticketId)}/triage/stream`, {
      method: "POST",
      headers: { Accept: "text/event-stream" },
      cache: "no-store",
    });
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
  if (!response.body) {
    throw new ApiRequestError("The triage stream could not be opened.", response.status, "STREAM_UNAVAILABLE");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  const trace: TraceStep[] = [];
  let buffer = "";
  let result: TriageResponse["result"] | null = null;
  let ticket: TriageResponse["ticket"] | null = null;

  const dispatch = (block: string) => {
    let event = "message";
    const data: string[] = [];
    for (const line of block.split("\n")) {
      if (line.startsWith("event:")) event = line.slice(6).trim();
      else if (line.startsWith("data:")) data.push(line.slice(5).trimStart());
    }
    if (!data.length) return;
    const payload = JSON.parse(data.join("\n")) as Record<string, unknown>;
    if (event === "trace") {
      const step = payload as unknown as TraceStep;
      trace.push(step);
      onTrace(step);
    } else if (event === "result") {
      result = payload as unknown as TriageResponse["result"];
    } else if (event === "done") {
      ticket = payload.ticket as TriageResponse["ticket"];
    } else if (event === "error") {
      const apiError = payload.error as ApiErrorPayload["error"] | undefined;
      throw new ApiRequestError(
        apiError?.message ?? "The AI service is temporarily unavailable.",
        502,
        apiError?.code ?? "LLM_UNAVAILABLE",
        trace,
      );
    }
  };

  try {
    while (true) {
      const { value, done } = await reader.read();
      buffer += decoder.decode(value, { stream: !done }).replace(/\r\n/g, "\n");
      let boundary = buffer.indexOf("\n\n");
      while (boundary !== -1) {
        dispatch(buffer.slice(0, boundary));
        buffer = buffer.slice(boundary + 2);
        boundary = buffer.indexOf("\n\n");
      }
      if (done) break;
    }
  } catch (error) {
    if (error instanceof ApiRequestError) throw error;
    throw new ApiRequestError("The triage stream ended unexpectedly.", 0, "STREAM_ERROR", trace);
  } finally {
    reader.releaseLock();
  }

  if (!result || !ticket) {
    throw new ApiRequestError("The triage stream ended before completion.", 0, "STREAM_INCOMPLETE", trace);
  }
  return { ticket, result, trace };
}
