"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { JoinForm } from "@/components/join-form";
import { getRegistration } from "@/lib/storage";

export default function HomePage() {
  const router = useRouter();
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    const { participantId, sessionCode } = getRegistration();
    if (participantId && sessionCode) {
      router.replace("/wall");
      return;
    }
    setChecking(false);
  }, [router]);

  if (checking) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <p className="text-sm text-[var(--color-muted-foreground)]">Cargando…</p>
      </main>
    );
  }

  return (
    <main className="min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-md rounded-2xl border border-[var(--color-border)] bg-[var(--color-card)] p-6 shadow-xl">
        <header className="mb-6">
          <h1 className="text-2xl font-bold">SkillWall Live</h1>
          <p className="text-sm text-[var(--color-muted-foreground)] mt-1">
            Comparte tus skills y dale like a las de otros.
          </p>
        </header>
        <JoinForm onJoined={() => router.replace("/wall")} />
      </div>
    </main>
  );
}
