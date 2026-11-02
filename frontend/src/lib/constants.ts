import type { ResolutionTag, TicketStatus } from "@/types";

export const TICKET_STATUS = {
  PENDING: "Pending",
  PROCESSING: "Processing",
  RESOLVED: "Resolved",
} as const satisfies Record<string, TicketStatus>;

export const STATUS_LABELS: Record<TicketStatus, string> = {
  [TICKET_STATUS.PENDING]: "Pending",
  [TICKET_STATUS.PROCESSING]: "Processing",
  [TICKET_STATUS.RESOLVED]: "Resolved",
};

export const STATUS_CLASSES: Record<TicketStatus, string> = {
  [TICKET_STATUS.PENDING]: "status-badge status-pending",
  [TICKET_STATUS.PROCESSING]: "status-badge status-processing",
  [TICKET_STATUS.RESOLVED]: "status-badge status-resolved",
};

export const TAG_CLASSES: Record<ResolutionTag, string> = {
  "Auto-Resolve": "tag-badge tag-auto-resolve",
  "Escalate to Sales": "tag-badge tag-escalate-sales",
};
