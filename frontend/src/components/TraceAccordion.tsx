"use client";

import { useEffect, useState } from "react";
import type { TraceStep } from "@/types";

interface TraceAccordionProps {
  trace: TraceStep[];
  isLive?: boolean;
}

function hasContent(value: unknown): boolean {
  if (value === undefined || value === null) return false;
  if (typeof value === "string") {
    const trimmed = value.trim();
    return trimmed.length > 0 && trimmed !== "No data recorded.";
  }
  if (typeof value === "object") {
    return Object.keys(value as object).length > 0;
  }
  return true;
}

function formatJson(value: unknown): string {
  if (typeof value === "string") {
    try {
      const parsed = JSON.parse(value);
      return JSON.stringify(parsed, null, 2);
    } catch {
      return value;
    }
  }
  return JSON.stringify(value, null, 2);
}

function stepBadgeStyle(step: TraceStep): { label: string; bgClass: string; textClass: string } {
  if (step.type === "tool_call") {
    return { label: "TOOL CALLED", bgClass: "bg-yellow", textClass: "text-ink" };
  }
  if (step.type === "tool_result") {
    return { label: "TOOL RESULT", bgClass: "bg-green", textClass: "text-ink" };
  }
  if (step.type === "error") {
    return { label: "STEP ERROR", bgClass: "bg-pink", textClass: "text-ink" };
  }
  if (step.type === "final") {
    return { label: "FINAL RESULT", bgClass: "bg-green", textClass: "text-ink" };
  }
  return { label: "AGENT REASONING", bgClass: "bg-blue", textClass: "text-white" };
}

export function TraceAccordion({ trace, isLive = false }: TraceAccordionProps) {
  const [isExpanded, setIsExpanded] = useState(isLive);
  const panelId = "agent-execution-trace-content";

  useEffect(() => {
    if (isLive) setIsExpanded(true);
  }, [isLive]);

  return (
    <section className={`trace-section ${isLive ? "is-live-trace" : ""}`}>
      <button
        type="button"
        className="trace-toggle"
        aria-expanded={isExpanded}
        aria-controls={panelId}
        onClick={() => setIsExpanded((current) => !current)}
      >
        <span>
          <span className="eyebrow">
            {isLive ? "● LIVE EXECUTION STREAM" : "Observability"} / {String(trace.length).padStart(2, "0")} STEPS
          </span>
          <strong>Agent Execution Trace</strong>
        </span>
        <span className="trace-toggle-indicator" aria-hidden="true">
          {isExpanded ? "−" : "+"}
        </span>
      </button>

      {isExpanded && (
        <div id={panelId} className="trace-content">
          {isLive && (
            <div className="trace-live-indicator" role="status" aria-live="polite">
              <span className="live-pulse-dot" aria-hidden="true" />
              <span>STREAMING AGENT EXECUTION TRACE IN REAL TIME...</span>
            </div>
          )}

          {trace.map((step, index) => {
            const badge = stepBadgeStyle(step);
            const isLast = index === trace.length - 1;
            const hasParams = hasContent(step.parameters);
            const hasRawOutput = hasContent(step.raw_output);
            const hasReasoning = hasContent(step.reasoning);

            return (
              <article
                className={`trace-step ${isLive && isLast ? "is-active-step" : ""}`}
                key={`${step.step}-${step.node}-${step.type}-${index}`}
              >
                <div className="trace-step-header">
                  <div className="trace-step-identity">
                    <span className="trace-step-num">{String(step.step).padStart(2, "0")}</span>
                    <div>
                      <div className="trace-step-meta">
                        <span className={`step-type-pill ${badge.bgClass} ${badge.textClass}`}>
                          {badge.label}
                        </span>
                        <span className="step-node-tag">node: {step.node}</span>
                        {step.tool && <span className="step-tool-tag">tool: {step.tool}</span>}
                      </div>
                      <h4 className="trace-step-title">
                        {step.tool ? `Tool Called: ${step.tool}` : badge.label}
                      </h4>
                    </div>
                  </div>

                  <div className="trace-step-stats">
                    <span className="step-duration">{step.duration_ms} ms</span>
                  </div>
                </div>

                <div className="trace-step-body">
                  {hasParams && (
                    <div className="trace-field-group">
                      <div className="trace-field-label">
                        <span>PARAMETERS</span>
                        <span className="field-type-hint">INPUT</span>
                      </div>
                      <div className="trace-terminal-card">
                        <pre className="trace-code">{formatJson(step.parameters)}</pre>
                      </div>
                    </div>
                  )}

                  {hasRawOutput && (
                    <div className="trace-field-group">
                      <div className="trace-field-label">
                        <span>RAW OUTPUT</span>
                        <span className="field-type-hint">TOOL RESULT</span>
                      </div>
                      <div className="trace-terminal-card">
                        <pre className="trace-code">{formatJson(step.raw_output)}</pre>
                      </div>
                    </div>
                  )}

                  {hasReasoning && (
                    <div className="trace-field-group">
                      <div className="trace-field-label">
                        <span>REASONING</span>
                        <span className="field-type-hint">AGENT THOUGHT</span>
                      </div>
                      <div className="trace-reasoning-card">
                        <p className="trace-reasoning-text">{step.reasoning}</p>
                      </div>
                    </div>
                  )}
                </div>

                <div className="trace-step-footer">
                  <span className="trace-timestamp">
                    Timestamp: {new Date(step.timestamp).toLocaleTimeString([], { hour12: true, hour: "2-digit", minute: "2-digit", second: "2-digit" })} UTC
                  </span>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}
