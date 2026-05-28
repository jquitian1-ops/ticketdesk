// Generate a W3C traceparent header value.
// Format: version-traceId(32hex)-spanId(16hex)-flags(2hex)
// Reference: https://www.w3.org/TR/trace-context/

function hex(bytes: number): string {
  const arr = new Uint8Array(bytes);
  if (typeof crypto !== "undefined" && crypto.getRandomValues) {
    crypto.getRandomValues(arr);
  } else {
    for (let i = 0; i < bytes; i++) arr[i] = Math.floor(Math.random() * 256);
  }
  return Array.from(arr, (b) => b.toString(16).padStart(2, "0")).join("");
}

export function generateTraceparent(): string {
  return `00-${hex(16)}-${hex(8)}-01`;
}
