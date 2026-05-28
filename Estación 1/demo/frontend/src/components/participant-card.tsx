"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import type { Participant } from "@/types";
import { SkillChip } from "./skill-chip";

interface ParticipantCardProps {
  readonly participant: Participant;
  readonly isSelf: boolean;
  readonly onLike: (targetParticipantId: string, skillId: string) => void;
}

export function ParticipantCard({ participant, isSelf, onLike }: ParticipantCardProps) {
  // Troubleshooting #30: <img> with onError fallback; next/image breaks S3 presigned URLs.
  const [imgFailed, setImgFailed] = useState(false);
  const photoSrc =
    !participant.photoUrl || imgFailed ? "/default-avatar.png" : participant.photoUrl;

  return (
    <article
      data-testid={`participant-card-${participant.participantId}`}
      className={cn(
        "rounded-xl border p-4 flex flex-col gap-3 transition-colors",
        "bg-[var(--color-card)] border-[var(--color-border)]",
        isSelf && "border-[var(--color-primary)] bg-[color-mix(in_oklab,var(--color-primary)_15%,var(--color-card))]"
      )}
    >
      <div className="flex items-center gap-3">
        <img
          src={photoSrc}
          alt={participant.displayName}
          onError={() => setImgFailed(true)}
          className="h-12 w-12 rounded-full object-cover bg-[var(--color-muted)]"
        />
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold truncate text-[var(--color-foreground)]">
            {participant.displayName}
            {isSelf && (
              <span className="ml-2 text-xs font-normal text-[var(--color-primary)]">(tú)</span>
            )}
          </h3>
          <p className="text-xs text-[var(--color-muted-foreground)]">
            {participant.totalLikes} likes
          </p>
        </div>
      </div>
      <div className="flex flex-wrap gap-2">
        {participant.skills.map((skill) => (
          <SkillChip
            key={skill.skillId}
            mode="like"
            skillId={skill.skillId}
            skillName={skill.skillName}
            likeCount={skill.likeCount}
            disabled={isSelf}
            onClick={() => onLike(participant.participantId, skill.skillId)}
          />
        ))}
      </div>
    </article>
  );
}
