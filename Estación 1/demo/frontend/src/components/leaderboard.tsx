"use client";

import { useState } from "react";
import type { LeaderEntry, SkillEntry } from "@/types";

interface LeaderboardProps {
  readonly topParticipants: LeaderEntry[];
  readonly topSkills: SkillEntry[];
}

function Avatar({ src, alt }: { readonly src: string; readonly alt: string }) {
  const [failed, setFailed] = useState(false);
  const resolved = !src || failed ? "/default-avatar.png" : src;
  return (
    <img
      src={resolved}
      alt={alt}
      onError={() => setFailed(true)}
      className="h-8 w-8 rounded-full object-cover bg-[var(--color-muted)]"
    />
  );
}

export function Leaderboard({ topParticipants, topSkills }: LeaderboardProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <section data-testid="leaderboard-participants">
        <h2 className="text-lg font-semibold mb-3 text-[var(--color-foreground)]">
          Top Participantes
        </h2>
        {topParticipants.length === 0 ? (
          <p className="text-sm text-[var(--color-muted-foreground)]">Sin datos aún</p>
        ) : (
          <ol className="space-y-2">
            {topParticipants.map((p, idx) => (
              <li
                key={p.participantId}
                data-testid={`leaderboard-participant-${p.participantId}`}
                className="flex items-center gap-3 p-2 rounded-lg bg-[var(--color-card)] border border-[var(--color-border)]"
              >
                <span className="w-6 text-sm font-bold text-[var(--color-muted-foreground)]">
                  #{idx + 1}
                </span>
                <Avatar src={p.photoUrl} alt={p.displayName} />
                <span className="flex-1 min-w-0 truncate text-sm font-medium">
                  {p.displayName}
                </span>
                <span className="text-sm font-semibold text-[var(--color-primary)]">
                  {p.totalLikes}
                </span>
              </li>
            ))}
          </ol>
        )}
      </section>

      <section data-testid="leaderboard-skills">
        <h2 className="text-lg font-semibold mb-3 text-[var(--color-foreground)]">
          Top Skills
        </h2>
        {topSkills.length === 0 ? (
          <p className="text-sm text-[var(--color-muted-foreground)]">Sin datos aún</p>
        ) : (
          <ol className="space-y-2">
            {topSkills.map((s, idx) => (
              <li
                key={s.skillId}
                data-testid={`leaderboard-skill-${s.skillId}`}
                className="flex items-center gap-3 p-2 rounded-lg bg-[var(--color-card)] border border-[var(--color-border)]"
              >
                <span className="w-6 text-sm font-bold text-[var(--color-muted-foreground)]">
                  #{idx + 1}
                </span>
                <span className="flex-1 min-w-0 truncate text-sm font-medium">
                  {s.skillName}
                </span>
                <span className="text-sm font-semibold text-[var(--color-primary)]">
                  {s.totalLikes}
                </span>
              </li>
            ))}
          </ol>
        )}
      </section>
    </div>
  );
}
