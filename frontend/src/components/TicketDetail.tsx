import { OutputCard } from "@/components/OutputCard";
import { TraceAccordion } from "@/components/TraceAccordion";
import { ErrorBox } from "@/components/ErrorBox";
import type { Ticket, TraceStep, TriageResult } from "@/types";

interface TicketDetailProps {
  ticket: Ticket;
  isRunning: boolean;
  result: TriageResult | null;
  trace: TraceStep[];
  errorMessage: string | null;
  onRunTriage: () => void;
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

export function TicketDetail({ ticket, isRunning, result, trace, errorMessage, onRunTriage }: TicketDetailProps) {
  return (
    <section className="panel ticket-detail" aria-labelledby="ticket-detail-heading" aria-busy={isRunning}>
      <div className="detail-topline">
        <p className="eyebrow">Selected ticket</p>
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
      </dl>
      <p className="detail-note">Review the customer message and ticket metadata before taking action.</p>

      <div className="agent-action-row">
        <div>
          <p className="eyebrow">Autonomous triage</p>
          <p className="agent-action-copy">The agent checks the ticket, uses approved support tools when needed, and prepares a customer reply.</p>
        </div>
        <button
          type="button"
          className="run-agent-button"
          onClick={onRunTriage}
          disabled={isRunning}
        >
          {isRunning ? (
            <><span className="button-spinner" aria-hidden="true" /> Agent is working</>
          ) : "Run AI Triage Agent"}
        </button>
      </div>

      {isRunning && (
        <p className="agent-progress" role="status" aria-live="polite">
          <span className="loading-indicator" aria-hidden="true" />
          The agent is reviewing this customer ticket. {trace.length > 0 && `${trace.length} trace ${trace.length === 1 ? "step" : "steps"} received.`}
        </p>
      )}
      {isRunning && trace.length > 0 && <TraceAccordion trace={trace} isLive />}
      {errorMessage && (
        <ErrorBox message={errorMessage} trace={trace} onRetry={onRunTriage} isRetrying={isRunning} />
      )}
      {result && (
        <div className="agent-result-stack">
          <OutputCard result={result} />
          <TraceAccordion trace={trace} />
        </div>
      )}
    </section>
  );
}
