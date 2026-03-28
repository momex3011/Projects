type UploadStage = "idle" | "uploading" | "processing" | "finished" | "error";

type ProgressBarProps = {
  value: number;
  label: string;
  stage: UploadStage;
};

const stageAccent: Record<UploadStage, string> = {
  idle: "from-[#8d91a8] via-[#b9b2cf] to-[#d2c2be]",
  uploading: "from-[var(--accent-coral)] via-[var(--accent-peach)] to-[var(--accent-sky)]",
  processing: "from-[var(--accent-peach)] via-[var(--accent-coral)] to-[var(--accent-mint)]",
  finished: "from-[var(--accent-mint)] via-[#a2efd8] to-[var(--accent-sky)]",
  error: "from-[#ff7f8f] via-[var(--accent-coral)] to-[var(--accent-peach)]",
};

export function ProgressBar({ value, label, stage }: ProgressBarProps) {
  const clampedValue = Math.max(0, Math.min(100, value));

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between gap-4 text-sm">
        <span className="text-[var(--text-muted)]">{label}</span>
        <span className="font-medium text-white">{Math.round(clampedValue)}%</span>
      </div>
      <div className="clay-inset relative h-5 overflow-hidden rounded-full p-1">
        <div
          className={`h-full rounded-full bg-gradient-to-r ${stageAccent[stage]} transition-[width] duration-500 ease-out`}
          style={{ width: `${clampedValue}%` }}
        />
        <div className="pointer-events-none absolute inset-y-1 left-3 right-3 rounded-full bg-[linear-gradient(90deg,transparent,rgba(255,255,255,0.22),transparent)] opacity-35" />
      </div>
    </div>
  );
}
