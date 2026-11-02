import { STATUS_CLASSES, STATUS_LABELS } from "@/lib/constants";
import type { TicketStatus } from "@/types";

interface StatusBadgeProps {
  status: TicketStatus;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  return (
    <span className={STATUS_CLASSES[status]}>
      <span aria-hidden="true" className="status-dot" />
      {STATUS_LABELS[status]}
    </span>
  );
}
