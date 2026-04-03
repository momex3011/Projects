"use client";

import {
  type FocusEvent,
  type ReactNode,
  useLayoutEffect,
  useRef,
  useState,
} from "react";
import { createPortal } from "react-dom";
import { Info } from "lucide-react";

import { cn } from "@/lib/utils";

type TooltipSide = "top" | "bottom" | "left" | "right" | "auto";

interface TooltipProps {
  content: ReactNode;
  children: ReactNode;
  side?: TooltipSide;
  className?: string;
}

type TooltipPlacement = Exclude<TooltipSide, "auto">;

const GAP = 12;
const VIEWPORT_MARGIN = 12;

function orderedPlacements(side: TooltipSide): TooltipPlacement[] {
  switch (side) {
    case "bottom":
      return ["bottom", "top", "right", "left"];
    case "left":
      return ["left", "right", "top", "bottom"];
    case "right":
      return ["right", "left", "top", "bottom"];
    case "top":
      return ["top", "bottom", "right", "left"];
    case "auto":
    default:
      return ["top", "bottom", "right", "left"];
  }
}

function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max);
}

function fitsPlacement(
  placement: TooltipPlacement,
  triggerRect: DOMRect,
  tooltipRect: DOMRect,
  viewportWidth: number,
  viewportHeight: number,
) {
  switch (placement) {
    case "top":
      return triggerRect.top >= tooltipRect.height + GAP + VIEWPORT_MARGIN;
    case "bottom":
      return viewportHeight - triggerRect.bottom >= tooltipRect.height + GAP + VIEWPORT_MARGIN;
    case "left":
      return triggerRect.left >= tooltipRect.width + GAP + VIEWPORT_MARGIN;
    case "right":
      return viewportWidth - triggerRect.right >= tooltipRect.width + GAP + VIEWPORT_MARGIN;
    default:
      return false;
  }
}

function placementScore(
  placement: TooltipPlacement,
  triggerRect: DOMRect,
  viewportWidth: number,
  viewportHeight: number,
) {
  switch (placement) {
    case "top":
      return triggerRect.top;
    case "bottom":
      return viewportHeight - triggerRect.bottom;
    case "left":
      return triggerRect.left;
    case "right":
      return viewportWidth - triggerRect.right;
    default:
      return 0;
  }
}

function calculatePosition(
  placement: TooltipPlacement,
  triggerRect: DOMRect,
  tooltipRect: DOMRect,
  viewportWidth: number,
  viewportHeight: number,
) {
  const centerX = triggerRect.left + triggerRect.width / 2;
  const centerY = triggerRect.top + triggerRect.height / 2;

  switch (placement) {
    case "top":
      return {
        top: triggerRect.top - tooltipRect.height - GAP,
        left: clamp(
          centerX - tooltipRect.width / 2,
          VIEWPORT_MARGIN,
          viewportWidth - tooltipRect.width - VIEWPORT_MARGIN,
        ),
      };
    case "bottom":
      return {
        top: triggerRect.bottom + GAP,
        left: clamp(
          centerX - tooltipRect.width / 2,
          VIEWPORT_MARGIN,
          viewportWidth - tooltipRect.width - VIEWPORT_MARGIN,
        ),
      };
    case "left":
      return {
        top: clamp(
          centerY - tooltipRect.height / 2,
          VIEWPORT_MARGIN,
          viewportHeight - tooltipRect.height - VIEWPORT_MARGIN,
        ),
        left: triggerRect.left - tooltipRect.width - GAP,
      };
    case "right":
    default:
      return {
        top: clamp(
          centerY - tooltipRect.height / 2,
          VIEWPORT_MARGIN,
          viewportHeight - tooltipRect.height - VIEWPORT_MARGIN,
        ),
        left: triggerRect.right + GAP,
      };
  }
}

export function Tooltip({
  content,
  children,
  side = "auto",
  className,
}: TooltipProps) {
  const triggerRef = useRef<HTMLSpanElement | null>(null);
  const tooltipRef = useRef<HTMLSpanElement | null>(null);
  const [isOpen, setIsOpen] = useState(false);
  const [position, setPosition] = useState<{
    top: number;
    left: number;
    placement: TooltipPlacement;
    ready: boolean;
  }>({
    top: 0,
    left: 0,
    placement: "top",
    ready: false,
  });
  const canUsePortal = typeof document !== "undefined";

  useLayoutEffect(() => {
    if (!canUsePortal || !isOpen || !triggerRef.current || !tooltipRef.current) {
      return;
    }

    const updatePosition = () => {
      if (!triggerRef.current || !tooltipRef.current) {
        return;
      }

      const triggerRect = triggerRef.current.getBoundingClientRect();
      const tooltipRect = tooltipRef.current.getBoundingClientRect();
      const viewportWidth = window.innerWidth;
      const viewportHeight = window.innerHeight;
      const placements = orderedPlacements(side);
      const placement =
        placements.find((candidate) =>
          fitsPlacement(
            candidate,
            triggerRect,
            tooltipRect,
            viewportWidth,
            viewportHeight,
          ),
        ) ??
        placements.sort(
          (leftPlacement, rightPlacement) =>
            placementScore(
              rightPlacement,
              triggerRect,
              viewportWidth,
              viewportHeight,
            ) -
            placementScore(
              leftPlacement,
              triggerRect,
              viewportWidth,
              viewportHeight,
            ),
        )[0];

      const nextPosition = calculatePosition(
        placement,
        triggerRect,
        tooltipRect,
        viewportWidth,
        viewportHeight,
      );

      setPosition({
        ...nextPosition,
        placement,
        ready: true,
      });
    };

    updatePosition();
    window.addEventListener("resize", updatePosition);
    window.addEventListener("scroll", updatePosition, true);

    return () => {
      window.removeEventListener("resize", updatePosition);
      window.removeEventListener("scroll", updatePosition, true);
    };
  }, [canUsePortal, content, isOpen, side]);

  const handleBlur = (event: FocusEvent<HTMLSpanElement>) => {
    const nextTarget = event.relatedTarget;

    if (!(nextTarget instanceof Node) || !event.currentTarget.contains(nextTarget)) {
      setIsOpen(false);
    }
  };

  return (
    <span
      ref={triggerRef}
      className={cn("relative inline-flex", className)}
      onMouseEnter={() => setIsOpen(true)}
      onMouseLeave={() => setIsOpen(false)}
      onFocusCapture={() => setIsOpen(true)}
      onBlurCapture={handleBlur}
    >
      {children}
      {canUsePortal && isOpen
        ? createPortal(
            <span
              ref={tooltipRef}
              role="tooltip"
              className={cn(
                "pointer-events-none fixed z-[120] max-w-[300px] rounded-[16px] border px-3.5 py-2.5 text-xs font-medium leading-5 shadow-2xl transition duration-150",
                position.ready ? "opacity-100" : "opacity-0",
              )}
              style={{
                top: position.top,
                left: position.left,
                background: "rgba(15, 23, 42, 0.98)",
                color: "#f8fafc",
                borderColor: "rgba(148, 163, 184, 0.28)",
                boxShadow:
                  "0 18px 42px rgba(15, 23, 42, 0.34), 0 2px 10px rgba(15, 23, 42, 0.18)",
              }}
            >
              {content}
            </span>,
            document.body,
          )
        : null}
    </span>
  );
}

export function HelpHint({
  content,
  label = "More info",
}: {
  content: ReactNode;
  label?: string;
}) {
  return (
    <Tooltip content={content}>
      <span
        tabIndex={0}
        aria-label={label}
        className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-600 shadow-clay-soft outline-none transition hover:text-slate-800 focus-visible:ring-2 focus-visible:ring-blue-200"
      >
        <Info className="h-4 w-4" />
      </span>
    </Tooltip>
  );
}
