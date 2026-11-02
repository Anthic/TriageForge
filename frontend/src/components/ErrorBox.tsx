import { TraceAccordion } from "@/components/TraceAccordion";
import type { TraceStep } from "@/types";

interface ErrorBoxProps {
  message: string;
  trace: TraceStep[];
  onRetry: () => void;
  isRetrying: boolean;
}

export function ErrorBox({ message, trace, onRetry, isRetrying }: ErrorBoxProps) {
  return (
    <section className="triage-error" role="alert" aria-live="assertive">
      <div className="triage-error-copy">
        <p className="eyebrow">Agent run / Failed</p>
        <h3>The agent could not complete this ticket.</h3>
        <p>{message}</p>
      </div>
      <button className="retry-button" type="button" onClick={onRetry} disabled={isRetrying}>
        {isRetrying ? "Retrying" : "Retry triage"}
      </button>
      {trace.length > 0 && <TraceAccordion trace={trace} />}
    </section>
  );
}
