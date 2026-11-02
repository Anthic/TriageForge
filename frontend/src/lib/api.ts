import type { ApiErrorPayload, Ticket } from "@/types";

const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

export class ApiRequestError extends Error {
  readonly status: number;
  readonly code: string;

  constructor(message: string, status: number, code: string) {
    super(message);
    this.name = "ApiRequestError";
    this.status = status;
    this.code = code;
  }
}

export async function getTickets(signal?: AbortSignal): Promise<Ticket[]> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/tickets`, { signal, cache: "no-store" });
  } catch {
    throw new ApiRequestError("Could not connect to the ticket service.", 0, "NETWORK_ERROR");
  }

  if (!response.ok) {
    const payload = (await response.json().catch(() => ({}))) as ApiErrorPayload;
    throw new ApiRequestError(
      payload.error?.message ?? "Could not load tickets.",
      response.status,
      payload.error?.code ?? "API_ERROR",
    );
  }

  return (await response.json()) as Ticket[];
}
