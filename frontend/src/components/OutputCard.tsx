import { TagBadge } from "@/components/TagBadge";
import type { TriageResult, TraceStep } from "@/types";

interface OutputCardProps {
  result: TriageResult;
  trace: TraceStep[];
}

interface Finding {
  label: string;
  value: string;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function getFindings(trace: TraceStep[]): Finding[] {
  const toolResult = [...trace].reverse().find((step) => step.type === "tool_result" && isRecord(step.raw_output));
  if (toolResult && isRecord(toolResult.raw_output)) {
    const output = toolResult.raw_output;
    if (toolResult.tool === "get_order_status") {
      return [
        ...(typeof output.order_id === "string" ? [{ label: "Order ID", value: output.order_id }] : []),
        ...(typeof output.status === "string" ? [{ label: "Status", value: output.status }] : []),
        ...(typeof output.est_delivery === "string" ? [{ label: "Estimated delivery", value: output.est_delivery }] : []),
      ];
    }
    if (toolResult.tool === "get_user_tier") {
      return [
        ...(typeof output.current_tier === "string" ? [{ label: "Current plan", value: output.current_tier }] : []),
        ...(typeof output.eligible_for_upgrade === "boolean"
          ? [{ label: "Upgrade eligibility", value: output.eligible_for_upgrade ? "Eligible" : "Not eligible" }]
          : []),
      ];
    }
  }

  const toolError = [...trace].reverse().find((step) => step.type === "error" && step.tool);
  if (toolError) {
    return [{ label: "Tool check", value: `${toolError.tool} could not be completed.` }];
  }
  return [{ label: "Support lookup", value: "No external support data was needed for this request." }];
}

export function OutputCard({ result, trace }: OutputCardProps) {
  const findings = getFindings(trace);
  const resolutionAction = result.tag === "Auto-Resolve"
    ? "Ready to resolve with the customer reply below."
    : "Route this request to the Sales team for follow-up.";

  return (
    <section className="agent-output" aria-labelledby="agent-output-heading" aria-live="polite">
      <header className="agent-output-heading">
        <div className="agent-identity">
          <span className="agent-avatar" aria-hidden="true">AI</span>
          <div>
            <p className="eyebrow">TriageForge / Completed analysis</p>
            <h3 id="agent-output-heading">Structured Triage Result</h3>
          </div>
        </div>
      </header>

      <div className="triage-result-sections">
        <section className="triage-result-section triage-decision">
          <div className="triage-section-heading">
            <span className="triage-section-number">01</span>
            <div>
              <p className="eyebrow">Decision</p>
              <h4>Recommended handling</h4>
            </div>
          </div>
          <div className="triage-decision-content">
            <TagBadge tag={result.tag} />
            <p>{resolutionAction}</p>
          </div>
        </section>

        <section className="triage-result-section">
          <div className="triage-section-heading">
            <span className="triage-section-number">02</span>
            <div>
              <p className="eyebrow">Evidence</p>
              <h4>Checks performed</h4>
            </div>
          </div>
          <dl className="triage-findings">
            {findings.map((finding) => (
              <div className="triage-finding" key={finding.label}>
                <dt>{finding.label}</dt>
                <dd>{finding.value}</dd>
              </div>
            ))}
          </dl>
        </section>

        <section className="triage-result-section triage-customer-reply">
          <div className="triage-section-heading">
            <span className="triage-section-number">03</span>
            <div>
              <p className="eyebrow">Customer-facing reply</p>
              <h4>Customer Response Draft</h4>
            </div>
          </div>
          <blockquote className="agent-draft">{result.draft}</blockquote>
        </section>

        <section className="triage-result-section triage-rationale-section">
          <div className="triage-section-heading">
            <span className="triage-section-number">04</span>
            <div>
              <p className="eyebrow">Internal summary</p>
              <h4>Why this outcome</h4>
            </div>
          </div>
          <p className="agent-reasoning">{result.reasoning}</p>
        </section>
      </div>
    </section>
  );
}
