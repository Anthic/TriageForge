import { StatusBadge } from "@/components/StatusBadge";
import type { Ticket } from "@/types";

interface TicketListProps {
  tickets: Ticket[];
  selectedTicketId: string | null;
  onSelect: (ticketId: string) => void;
}

export function TicketList({ tickets, selectedTicketId, onSelect }: TicketListProps) {
  return (
    <section className="panel ticket-list-panel" aria-labelledby="ticket-queue-heading">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Inbox / 01</p>
          <h2 id="ticket-queue-heading">Ticket queue</h2>
        </div>
        <span className="count-chip" aria-label={`${tickets.length} tickets`}>
          {String(tickets.length).padStart(2, "0")}
        </span>
      </div>

      {tickets.length === 0 ? (
        <p className="empty-state">No tickets found.</p>
      ) : (
        <ul className="ticket-list">
          {tickets.map((ticket) => {
            const selected = ticket.id === selectedTicketId;
            return (
              <li key={ticket.id}>
                <button
                  type="button"
                  className={`ticket-select${selected ? " is-selected" : ""}`}
                  onClick={() => onSelect(ticket.id)}
                  aria-pressed={selected}
                  aria-current={selected ? "true" : undefined}
                >
                  <span className="ticket-select-topline">
                    <span className="ticket-id">{ticket.id}</span>
                    <StatusBadge status={ticket.status} />
                  </span>
                  <span className="ticket-preview">{ticket.text}</span>
                  <span className="ticket-customer">Customer {ticket.user_id}</span>
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
