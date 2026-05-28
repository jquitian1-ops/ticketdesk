import type { APIGatewayProxyEventV2, APIGatewayProxyStructuredResultV2 } from "aws-lambda";

// Troubleshooting #2: API Gateway HTTP API v2 may send body base64-encoded
// (depends on Content-Type). Always decode when isBase64Encoded is true.
export function parseBody<T = unknown>(event: APIGatewayProxyEventV2): T {
  if (!event.body) {
    return {} as T;
  }
  const raw = event.isBase64Encoded ? Buffer.from(event.body, "base64").toString("utf-8") : event.body;
  if (!raw) {
    return {} as T;
  }
  try {
    return JSON.parse(raw) as T;
  } catch {
    throw new HttpError(400, "Invalid JSON body");
  }
}

// Troubleshooting #20: API Gateway HTTP v2 manages CORS at the API level.
// DO NOT set Access-Control-Allow-Origin or related headers here — API Gateway
// will overwrite them (and they could cause duplicate-header errors).
export function json(statusCode: number, body: unknown): APIGatewayProxyStructuredResultV2 {
  return {
    statusCode,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  };
}

export class HttpError extends Error {
  constructor(public statusCode: number, public message: string, public details?: unknown) {
    super(message);
  }
}

export function error(statusCode: number, message: string, details?: unknown): APIGatewayProxyStructuredResultV2 {
  return json(statusCode, { error: message, ...(details ? { details } : {}) });
}

export function getQuery(event: APIGatewayProxyEventV2, key: string): string | undefined {
  return event.queryStringParameters?.[key];
}

export function getPathParam(event: APIGatewayProxyEventV2, key: string): string | undefined {
  return event.pathParameters?.[key];
}

export function getHeader(event: APIGatewayProxyEventV2, key: string): string | undefined {
  const headers = event.headers ?? {};
  const lower = key.toLowerCase();
  for (const [k, v] of Object.entries(headers)) {
    if (k.toLowerCase() === lower) return v;
  }
  return undefined;
}

export function getRouteKey(event: APIGatewayProxyEventV2): string {
  return event.requestContext?.http
    ? `${event.requestContext.http.method} ${event.requestContext.http.path}`
    : event.routeKey ?? "";
}

export function getMethod(event: APIGatewayProxyEventV2): string {
  return event.requestContext?.http?.method ?? "GET";
}

export function getPath(event: APIGatewayProxyEventV2): string {
  return event.requestContext?.http?.path ?? event.rawPath ?? "/";
}
