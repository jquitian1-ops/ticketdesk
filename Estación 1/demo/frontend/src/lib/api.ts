import { generateTraceparent } from "./trace";
import type {
  JoinResponse,
  LeaderboardResponse,
  LikeResponse,
  UploadUrlResponse,
  WallResponse
} from "@/types";

// Troubleshooting #14: API URL must never have a trailing slash, otherwise
// `${API_BASE}/join` becomes `...amazonaws.com//join` and routes 404.
// Strip aggressively at the edge so the rest of the app can assume a clean base.
const RAW_BASE =
  process.env.NEXT_PUBLIC_API_URL ??
  "https://6svkxadr3h.execute-api.us-east-1.amazonaws.com";
export const API_BASE = RAW_BASE.replace(/\s+/g, "").replace(/\/+$/, "");

export const SESSION_CODE =
  (process.env.NEXT_PUBLIC_SESSION_CODE ?? "LATAM2026").trim();

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`;
  const headers = new Headers(init?.headers);
  if (!headers.has("Content-Type") && init?.body) {
    headers.set("Content-Type", "application/json");
  }
  headers.set("traceparent", generateTraceparent());

  const res = await fetch(url, { ...init, headers });
  const text = await res.text();
  let body: unknown = null;
  if (text) {
    try {
      body = JSON.parse(text);
    } catch {
      // Non-JSON body — fall through.
    }
  }
  if (!res.ok) {
    const errMsg =
      (body as { error?: string } | null)?.error ?? `Request failed (${res.status})`;
    throw new ApiError(res.status, errMsg);
  }
  return body as T;
}

export class ApiError extends Error {
  constructor(public readonly status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

export async function getUploadUrl(args: {
  sessionCode: string;
  contentType: string;
}): Promise<UploadUrlResponse> {
  return request<UploadUrlResponse>("/upload-url", {
    method: "POST",
    body: JSON.stringify(args)
  });
}

export async function uploadToS3(uploadUrl: string, file: File): Promise<void> {
  const res = await fetch(uploadUrl, {
    method: "PUT",
    headers: { "Content-Type": file.type },
    body: file
  });
  if (!res.ok) {
    throw new ApiError(res.status, "Photo upload failed");
  }
}

export async function joinSession(args: {
  sessionCode: string;
  displayName: string;
  skills: string[];
  photoObjectKey?: string;
}): Promise<JoinResponse> {
  return request<JoinResponse>("/join", {
    method: "POST",
    body: JSON.stringify({ photoObjectKey: "", ...args })
  });
}

export async function getWall(
  sessionCode: string,
  sort: "new" | "top"
): Promise<WallResponse> {
  const qs = new URLSearchParams({ sessionCode, sort });
  return request<WallResponse>(`/wall?${qs.toString()}`);
}

export async function getLeaderboard(
  sessionCode: string
): Promise<LeaderboardResponse> {
  const qs = new URLSearchParams({ sessionCode });
  return request<LeaderboardResponse>(`/leaderboard?${qs.toString()}`);
}

export async function likeSkill(args: {
  sessionCode: string;
  voterId: string;
  targetParticipantId: string;
  skillId: string;
}): Promise<LikeResponse> {
  return request<LikeResponse>("/like", {
    method: "POST",
    body: JSON.stringify(args)
  });
}
