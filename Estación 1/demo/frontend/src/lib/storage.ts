export const STORAGE_KEYS = {
  participantId: "skillwall_participantId",
  sessionCode: "skillwall_sessionCode"
} as const;

export function getStored(key: string): string | null {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage.getItem(key);
  } catch {
    return null;
  }
}

export function setStored(key: string, value: string): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(key, value);
  } catch {
    // Quota exceeded / private mode — fail silently
  }
}

export function clearStored(key: string): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.removeItem(key);
  } catch {
    // ignore
  }
}

export function getRegistration(): {
  participantId: string | null;
  sessionCode: string | null;
} {
  return {
    participantId: getStored(STORAGE_KEYS.participantId),
    sessionCode: getStored(STORAGE_KEYS.sessionCode)
  };
}

export function setRegistration(participantId: string, sessionCode: string): void {
  setStored(STORAGE_KEYS.participantId, participantId);
  setStored(STORAGE_KEYS.sessionCode, sessionCode);
}
