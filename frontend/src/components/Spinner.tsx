interface SpinnerProps {
  size?: "sm" | "md";
  className?: string;
  label?: string;
}

export function Spinner({ size = "md", className = "", label }: SpinnerProps) {
  if (size === "sm") {
    return (
      <span className={`brutalist-stepper-sm ${className}`.trim()} aria-hidden="true" title={label}>
        <span className="stepper-dot dot-1" />
        <span className="stepper-dot dot-2" />
        <span className="stepper-dot dot-3" />
      </span>
    );
  }

  return (
    <div className={`brutalist-meter-md ${className}`.trim()} role="progressbar" aria-label={label ?? "Loading"}>
      <span className="meter-block block-1" />
      <span className="meter-block block-2" />
      <span className="meter-block block-3" />
      <span className="meter-block block-4" />
    </div>
  );
}
