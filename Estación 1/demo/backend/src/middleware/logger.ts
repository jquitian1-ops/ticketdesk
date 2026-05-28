// Structured JSON logger with traceId correlation.
// Events: SESSION_CREATED, SESSION_DELETED, JOIN_CREATED, LIKE_CAST,
// IDEMPOTENT_LIKE, VALIDATION_FAILED, RATE_LIMITED, HEALTH_CHECK_FAILED, ERROR
export type LogLevel = "info" | "warn" | "error";

export interface LogContext {
  traceId?: string;
  spanId?: string;
  sessionCode?: string;
  participantId?: string;
  routeKey?: string;
  [key: string]: unknown;
}

function emit(level: LogLevel, event: string, ctx: LogContext = {}): void {
  const record = { level, event, timestamp: new Date().toISOString(), ...ctx };
  const line = JSON.stringify(record);
  if (level === "error") console.error(line);
  else if (level === "warn") console.warn(line);
  else console.log(line);
}

export const logger = {
  info: (event: string, ctx?: LogContext) => emit("info", event, ctx),
  warn: (event: string, ctx?: LogContext) => emit("warn", event, ctx),
  error: (event: string, ctx?: LogContext) => emit("error", event, ctx)
};
