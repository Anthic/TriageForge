import { StatusBadge } from "@/components/StatusBadge";
import type { Ticket } from "@/types";

interface TicketDetailProps {
  ticket: Ticket;
}

function formatDate(value: string): string {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "Date unavailable";
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "UTC",
  }).format(parsed);
}

export function TicketDetail({ ticket }: TicketDetailProps) {
  return (
    <section className="panel ticket-detail" aria-labelledby="ticket-detail-heading">
      <div className="detail-topline">
        <p className="eyebrow">Selected ticket / {ticket.id}</p>
        <StatusBadge status={ticket.status} />
      </div>
      <h2 id="ticket-detail-heading" className="detail-title">Customer message</h2>
      <blockquote className="customer-message">{ticket.text}</blockquote>

      <div className="metadata-heading">
        <p className="eyebrow">Ticket record</p>
        <span className="metadata-rule" aria-hidden="true" />
      </div>
      <dl className="metadata-grid">
        <div className="metadata-item">
          <dt>Ticket ID</dt>
          <dd>{ticket.id}</dd>
        </div>
        <div className="metadata-item">
          <dt>Customer ID</dt>
          <dd>{ticket.user_id}</dd>
        </div>
        <div className="metadata-item">
          <dt>Order ID</dt>
          <dd>{ticket.order_id ?? "Not provided"}</dd>
        </div>
        <div className="metadata-item">
          <dt>Created</dt>
          <dd>{formatDate(ticket.created_at)} UTC</dd>
        </div>
        <div className="metadata-item metadata-item-wide">
          <dt>Current status</dt>
          <dd><StatusBadge status={ticket.status} /></dd>
        </div>
      </dl>
      <p className="detail-note">Review the customer message and ticket metadata before taking action.</p>
    </section>
  );
}
