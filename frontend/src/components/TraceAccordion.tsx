"use client";

import { useState } from "react";
import type { TraceStep } from "@/types";

interface TraceAccordionProps {
  trace: TraceStep[];
}

function formatValue(value: unknown): string {
  if (value === undefined || value === null) return "No data recorded.";
  if (typeof value === "string") return value;
  return JSON.stringify(value, null, 2) ?? "No data recorded.";
}

function stepLabel(step: TraceStep): string {
  if (step.type === "tool_call") return "Tool Called";
  if (step.type === "tool_result") return "Tool Result";
  if (step.type === "error") return "Error";
  if (step.type === "final") return "Agent Result";
  return "Agent Reasoning";
}

export function TraceAccordion({ trace }: TraceAccordionProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const panelId = "agent-execution-trace-content";

  return (
    <section className="trace-section">
      <button
        type="button"
        className="trace-toggle"
        aria-expanded={isExpanded}
        aria-controls={panelId}
        onClick={() => setIsExpanded((current) => !current)}
      >
        <span>
          <span className="eyebrow">Observability / {String(trace.length).padStart(2, "0")} steps</span>
          <strong>Agent Execution Trace</strong>
        </span>
        <span className="trace-toggle-indicator" aria-hidden="true">{isExpanded ? "−" : "+"}</span>
      </button>
      {isExpanded && (
        <div id={panelId} className="trace-content">
          {trace.map((step) => (
            <article className="trace-step" key={`${step.step}-${step.node}-${step.type}`}>
              <div className="trace-step-heading">
                <span className="trace-step-number">{String(step.step).padStart(2, "0")}</span>
                <div>
                  <h4>{stepLabel(step)}</h4>
                  <p>{step.node}{step.tool ? ` / ${step.tool}` : ""} / {step.duration_ms} ms</p>
                </div>
              </div>
              {step.parameters && (
                <TraceValue label="Parameters" value={step.parameters} />
              )}
              {step.raw_output !== undefined && (
                <TraceValue label="Raw Output" value={step.raw_output} />
              )}
              {step.reasoning && <TraceValue label="Reasoning" value={step.reasoning} />}
              <p className="trace-timestamp">{new Date(step.timestamp).toLocaleString()}</p>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

interface TraceValueProps {
  label: string;
  value: unknown;
}

function TraceValue({ label, value }: TraceValueProps) {
  return (
    <div className="trace-value">
      <h5>{label}</h5>
      <pre>{formatValue(value)}</pre>
    </div>
  );
}
