// Mock services + presigner so the router walks through without AWS calls.
jest.mock("@aws-sdk/s3-request-presigner", () => ({
  getSignedUrl: jest.fn().mockResolvedValue("https://signed.example.com/abc")
}));
jest.mock("../src/services/dynamodb", () => ({
  describeTable: jest.fn().mockResolvedValue({ status: "ACTIVE" }),
  getSession: jest.fn().mockResolvedValue(null),
  putSession: jest
    .fn()
    .mockImplementation(async (sessionCode: string) => ({
      PK: `SESSION#${sessionCode}`,
      SK: "METADATA",
      sessionCode,
      createdAt: "2026-05-11T00:00:00.000Z"
    })),
  getParticipant: jest.fn().mockResolvedValue(null),
  putParticipant: jest.fn().mockResolvedValue(undefined),
  queryParticipants: jest.fn().mockResolvedValue([]),
  batchDeleteSession: jest.fn().mockResolvedValue(0),
  incrementSkillLike: jest.fn().mockResolvedValue({ alreadyVoted: false }),
  deleteSessionMetadata: jest.fn()
}));

import { handler } from "../src/index";

function makeEvent(method: string, path: string, overrides: Record<string, unknown> = {}): any {
  return {
    routeKey: `${method} ${path}`,
    rawPath: path,
    headers: {},
    requestContext: { http: { method, path }, requestId: "test-req-id" },
    isBase64Encoded: false,
    ...overrides
  };
}

const ctx: any = { awsRequestId: "test-trace-id" };

describe("Lambda handler routing", () => {
  it("returns 200 for GET /health", async () => {
    const result = await handler(makeEvent("GET", "/health"), ctx);
    expect(result.statusCode).toBe(200);
  });

  it("returns 404 for unknown route", async () => {
    const result = await handler(makeEvent("GET", "/nope"), ctx);
    expect(result.statusCode).toBe(404);
  });

  it("routes DELETE /admin/sessions/{code} to admin-delete handler", async () => {
    const result = await handler(
      makeEvent("DELETE", "/admin/sessions/S1", {
        headers: { authorization: "Bearer test-admin-token" },
        pathParameters: { code: "S1" }
      }),
      ctx
    );
    expect(result.statusCode).toBe(200);
  });

  it("response has Content-Type but no CORS headers (troubleshooting #20)", async () => {
    const result = await handler(makeEvent("GET", "/health"), ctx);
    const headers = result.headers ?? {};
    expect(headers["Content-Type"]).toBe("application/json");
    // CORS must NOT be set by Lambda — API Gateway handles it.
    expect(headers["Access-Control-Allow-Origin"]).toBeUndefined();
    expect(headers["access-control-allow-origin"]).toBeUndefined();
  });
});
