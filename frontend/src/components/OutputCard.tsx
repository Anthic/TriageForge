import { TagBadge } from "@/components/TagBadge";
import type { TriageResult } from "@/types";

interface OutputCardProps {
  result: TriageResult;
}

export function OutputCard({ result }: OutputCardProps) {
  return (
    <section className="agent-output" aria-labelledby="agent-output-heading" aria-live="polite">
      <div className="agent-output-heading">
        <div className="agent-identity">
          <span className="agent-avatar" aria-hidden="true">AI</span>
          <div>
            <p className="eyebrow">TriageForge / Agent response</p>
            <h3 id="agent-output-heading">Customer Response Draft</h3>
          </div>
        </div>
        <div className="result-tag">
          <span className="eyebrow">Resolution tag</span>
          <TagBadge tag={result.tag} />
        </div>
      </div>
      <p className="agent-draft">{result.draft}</p>
      <p className="agent-reasoning-label">Resolution summary</p>
      <p className="agent-reasoning">{result.reasoning}</p>
    </section>
  );
}
