import type { ReactNode } from "react";

import { HelpHint } from "@/components/ui/Tooltip";

interface PanelTitleProps {
  eyebrow?: string;
  title: string;
  description?: string;
  trailing?: ReactNode;
  helpText?: string;
}

export function PanelTitle({
  eyebrow,
  title,
  description,
  trailing,
  helpText,
}: PanelTitleProps) {
  return (
    <div className="flex items-start justify-between gap-4">
      <div className="space-y-1">
        {eyebrow ? (
          <p className="text-[10px] font-semibold uppercase tracking-[0.34em] text-slate-600">
            {eyebrow}
          </p>
        ) : null}
        <div className="flex items-center gap-2">
          <h2 className="text-lg font-semibold text-slate-800">
            {title}
          </h2>
          {helpText ? <HelpHint content={helpText} label={`${title} help`} /> : null}
        </div>
        {description ? (
          <p className="max-w-xl text-sm leading-6 text-slate-600">
            {description}
          </p>
        ) : null}
      </div>
      {trailing}
    </div>
  );
}
