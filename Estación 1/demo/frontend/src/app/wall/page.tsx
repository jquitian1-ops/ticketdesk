"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { getLeaderboard, getWall, likeSkill } from "@/lib/api";
import { clearStored, getRegistration, STORAGE_KEYS } from "@/lib/storage";
import { ParticipantCard } from "@/components/participant-card";
import { Leaderboard } from "@/components/leaderboard";
import type { LeaderEntry, Participant, SkillEntry } from "@/types";
import { cn } from "@/lib/utils";

type Tab = "wall" | "leaderboard";
type Sort = "new" | "top";

const POLL_MS = 2000;

export default function WallPage() {
  const router = useRouter();
  const [tab, setTab] = useState<Tab>("wall");
  const [sort, setSort] = useState<Sort>("new");
  const [participants, setParticipants] = useState<Participant[]>([]);
  const [topParticipants, setTopParticipants] = useState<LeaderEntry[]>([]);
  const [topSkills, setTopSkills] = useState<SkillEntry[]>([]);
  const [me, setMe] = useState<{ participantId: string; sessionCode: string } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const pollRef = useRef<number | null>(null);

  useEffect(() => {
    const { participantId, sessionCode } = getRegistration();
    if (!participantId || !sessionCode) {
      router.replace("/");
      return;
    }
    setMe({ participantId, sessionCode });
  }, [router]);

  const refresh = useCallback(
    async (sessionCode: string, currentSort: Sort) => {
      try {
        const [wallRes, lbRes] = await Promise.all([
          getWall(sessionCode, currentSort),
          getLeaderboard(sessionCode)
        ]);
        setParticipants(wallRes.items);
        setTopParticipants(lbRes.topParticipants);
        setTopSkills(lbRes.topSkills);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Error al cargar");
      }
    },
    []
  );

  useEffect(() => {
    if (!me) return;
    refresh(me.sessionCode, sort);
    pollRef.current = window.setInterval(() => {
      refresh(me.sessionCode, sort);
    }, POLL_MS);
    return () => {
      if (pollRef.current !== null) window.clearInterval(pollRef.current);
    };
  }, [me, sort, refresh]);

  const onLike = useCallback(
    async (targetParticipantId: string, skillId: string) => {
      if (!me) return;
      try {
        await likeSkill({
          sessionCode: me.sessionCode,
          voterId: me.participantId,
          targetParticipantId,
          skillId
        });
        refresh(me.sessionCode, sort);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Error al dar like");
      }
    },
    [me, sort, refresh]
  );

  const logout = useCallback(() => {
    clearStored(STORAGE_KEYS.participantId);
    clearStored(STORAGE_KEYS.sessionCode);
    router.replace("/");
  }, [router]);

  if (!me) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <p className="text-sm text-[var(--color-muted-foreground)]">Cargando…</p>
      </main>
    );
  }

  return (
    <main className="min-h-screen p-4 max-w-5xl mx-auto">
      <header className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-bold">SkillWall Live</h1>
        <button
          type="button"
          data-testid="logout-button"
          onClick={logout}
          className="text-xs text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)] transition-colors"
        >
          Salir
        </button>
      </header>

      <nav className="flex gap-2 mb-4">
        <button
          type="button"
          data-testid="tab-wall"
          onClick={() => setTab("wall")}
          className={cn(
            "px-3 py-1.5 rounded-lg text-sm font-medium transition-colors",
            tab === "wall"
              ? "bg-[var(--color-primary)] text-white"
              : "bg-[var(--color-card)] text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)]"
          )}
        >
          Wall
        </button>
        <button
          type="button"
          data-testid="tab-leaderboard"
          onClick={() => setTab("leaderboard")}
          className={cn(
            "px-3 py-1.5 rounded-lg text-sm font-medium transition-colors",
            tab === "leaderboard"
              ? "bg-[var(--color-primary)] text-white"
              : "bg-[var(--color-card)] text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)]"
          )}
        >
          Leaderboard
        </button>
      </nav>

      {error && (
        <div className="mb-3 px-3 py-2 rounded-lg border border-[var(--color-danger)] bg-[color-mix(in_oklab,var(--color-danger)_15%,transparent)] text-sm text-[var(--color-danger)]">
          {error}
        </div>
      )}

      {tab === "wall" && (
        <>
          <div className="flex gap-2 mb-3">
            <button
              type="button"
              data-testid="sort-new"
              onClick={() => setSort("new")}
              className={cn(
                "px-2.5 py-1 rounded-md text-xs font-medium transition-colors",
                sort === "new"
                  ? "bg-[var(--color-accent)] text-black"
                  : "bg-[var(--color-card)] text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)]"
              )}
            >
              Recientes
            </button>
            <button
              type="button"
              data-testid="sort-top"
              onClick={() => setSort("top")}
              className={cn(
                "px-2.5 py-1 rounded-md text-xs font-medium transition-colors",
                sort === "top"
                  ? "bg-[var(--color-accent)] text-black"
                  : "bg-[var(--color-card)] text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)]"
              )}
            >
              Top
            </button>
          </div>

          {participants.length === 0 ? (
            <p className="text-sm text-[var(--color-muted-foreground)]">
              Aún no hay participantes. Sé el primero en sumarte.
            </p>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {participants.map((p) => (
                <ParticipantCard
                  key={p.participantId}
                  participant={p}
                  isSelf={p.participantId === me.participantId}
                  onLike={onLike}
                />
              ))}
            </div>
          )}
        </>
      )}

      {tab === "leaderboard" && (
        <Leaderboard topParticipants={topParticipants} topSkills={topSkills} />
      )}
    </main>
  );
}
