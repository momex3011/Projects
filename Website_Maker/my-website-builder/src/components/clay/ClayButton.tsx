import type { ButtonHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

interface ClayButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "ghost" | "accent";
}

export function ClayButton({
  className,
  variant = "primary",
  ...props
}: ClayButtonProps) {
  return (
    <button
      className={cn(
        "clay-button",
        variant === "ghost" && "clay-button-ghost",
        variant === "accent" && "clay-button-accent",
        className,
      )}
      {...props}
    />
  );
}
