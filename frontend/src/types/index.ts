export type TicketStatus = "Pending" | "Processing" | "Resolved";

export interface Ticket {
  id: string;
  user_id: string;
  order_id: string | null;
  text: string;
  status: TicketStatus;
  created_at: string;
}

export interface ApiErrorPayload {
  error?: {
    code?: string;
    message?: string;
  };
}
