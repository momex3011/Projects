import type { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export function ClayCard({
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("clay-panel", className)} {...props} />;
}
