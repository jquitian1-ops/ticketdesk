"use client";

import { Heart } from "lucide-react";
import { cn } from "@/lib/utils";

interface SkillChipProps {
  readonly skillId: string;
  readonly skillName: string;
  readonly likeCount?: number;
  readonly selected?: boolean;
  readonly disabled?: boolean;
  readonly mode: "select" | "like";
  readonly onClick?: () => void;
}

export function SkillChip({
  skillId,
  skillName,
  likeCount = 0,
  selected = false,
  disabled = false,
  mode,
  onClick
}: SkillChipProps) {
  if (mode === "select") {
    return (
      <button
        type="button"
        data-testid={`skill-chip-${skillId}`}
        onClick={onClick}
        disabled={disabled}
        className={cn(
          "px-3 py-1.5 rounded-full text-sm font-medium border transition-colors",
          "border-[var(--color-border)] bg-[var(--color-card)] text-[var(--color-foreground)]",
          selected && "bg-[var(--color-primary)] text-white border-[var(--color-primary)]",
          disabled && !selected && "opacity-40 cursor-not-allowed"
        )}
      >
        {skillName}
      </button>
    );
  }

  return (
    <button
      type="button"
      data-testid={`skill-chip-${skillId}`}
      onClick={onClick}
      disabled={disabled}
      className={cn(
        "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border transition-colors",
        "border-[var(--color-border)] bg-[var(--color-card)] text-[var(--color-foreground)]",
        !disabled && "hover:border-[var(--color-accent)] hover:text-[var(--color-accent)]",
        disabled && "opacity-50 cursor-not-allowed"
      )}
    >
      <span>{skillName}</span>
      <span className="inline-flex items-center gap-0.5 text-[var(--color-muted-foreground)]">
        <Heart className="h-3 w-3" aria-hidden="true" />
        <span data-testid={`skill-like-count-${skillId}`}>{likeCount}</span>
      </span>
    </button>
  );
}
