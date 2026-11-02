import type { TicketStatus } from "@/types";

export const STATUS_LABELS: Record<TicketStatus, string> = {
  Pending: "Pending",
  Processing: "Processing",
  Resolved: "Resolved",
};

export const STATUS_CLASSES: Record<TicketStatus, string> = {
  Pending: "status-badge status-pending",
  Processing: "status-badge status-processing",
  Resolved: "status-badge status-resolved",
};
