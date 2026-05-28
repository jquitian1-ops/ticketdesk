// Troubleshooting #7: Mock @aws-sdk/s3-request-presigner BEFORE importing handlers
// to avoid Node 22 + Jest dynamic-import crash.
jest.mock("@aws-sdk/s3-request-presigner", () => ({
  getSignedUrl: jest.fn().mockResolvedValue("https://signed.example.com/abc")
}));

// Mock services so handlers don't hit AWS.
jest.mock("../src/services/dynamodb", () => ({
  describeTable: jest.fn().mockResolvedValue({ status: "ACTIVE" }),
  getSession: jest.fn(),
  putSession: jest
    .fn()
    .mockImplementation(async (sessionCode: string) => ({
      PK: `SESSION#${sessionCode}`,
      SK: "METADATA",
      sessionCode,
      createdAt: "2026-05-11T00:00:00.000Z"
    })),
  getParticipant: jest.fn(),
  putParticipant: jest.fn().mockResolvedValue(undefined),
  queryParticipants: jest.fn().mockResolvedValue([]),
  batchDeleteSession: jest.fn().mockResolvedValue(0),
  incrementSkillLike: jest.fn().mockResolvedValue({ alreadyVoted: false }),
  deleteSessionMetadata: jest.fn()
}));

import { handleHealth } from "../src/handlers/health";
import { handleUploadUrl } from "../src/handlers/upload-url";
import { handleJoin } from "../src/handlers/join";
import { handleWall } from "../src/handlers/wall";
import { handleLeaderboard } from "../src/handlers/leaderboard";
import { handleAdminCreate } from "../src/handlers/admin-create";
import { handleAdminDelete } from "../src/handlers/admin-delete";
import * as ddb from "../src/services/dynamodb";

function makeEvent(overrides: Record<string, unknown> = {}): any {
  return {
    routeKey: "$default",
    rawPath: "/",
    headers: {},
    requestContext: { http: { method: "GET", path: "/" } },
    isBase64Encoded: false,
    ...overrides
  };
}

describe("handlers", () => {
  describe("health", () => {
    it("returns ok status when DynamoDB is reachable", async () => {
      const result = await handleHealth(makeEvent());
      expect(result.statusCode).toBe(200);
      const body = JSON.parse(result.body ?? "{}");
      expect(body.status).toBe("ok");
      expect(body.dynamodb).toBe("ok");
    });
  });

  describe("upload-url", () => {
    it("returns 400 on validation failure", async () => {
      const result = await handleUploadUrl(
        makeEvent({ body: JSON.stringify({ sessionCode: "bad code!", contentType: "image/jpeg" }) })
      );
      expect(result.statusCode).toBe(400);
    });

    it("returns objectKey and uploadUrl on success", async () => {
      const result = await handleUploadUrl(
        makeEvent({
          body: JSON.stringify({ sessionCode: "LATAM2026", contentType: "image/jpeg" })
        })
      );
      expect(result.statusCode).toBe(200);
      const body = JSON.parse(result.body ?? "{}");
      expect(body.objectKey).toMatch(/^LATAM2026\/[0-9a-f]{24}\.jpg$/);
      expect(body.uploadUrl).toBe("https://signed.example.com/abc");
    });

    it("decodes base64 body (troubleshooting #2)", async () => {
      const payload = { sessionCode: "LATAM2026", contentType: "image/png" };
      const encoded = Buffer.from(JSON.stringify(payload)).toString("base64");
      const result = await handleUploadUrl(makeEvent({ body: encoded, isBase64Encoded: true }));
      expect(result.statusCode).toBe(200);
      const body = JSON.parse(result.body ?? "{}");
      expect(body.objectKey).toMatch(/\.png$/);
    });
  });

  describe("join (troubleshooting #32)", () => {
    it("returns 404 if session does not exist", async () => {
      (ddb.getSession as jest.Mock).mockResolvedValueOnce(null);
      const result = await handleJoin(
        makeEvent({
          body: JSON.stringify({
            sessionCode: "MISSING",
            displayName: "Ana",
            skills: ["1", "2", "3"]
          })
        })
      );
      expect(result.statusCode).toBe(404);
    });

    it("creates participant with empty photoObjectKey (troubleshooting #13)", async () => {
      (ddb.getSession as jest.Mock).mockResolvedValueOnce({
        PK: "SESSION#S1",
        SK: "METADATA",
        sessionCode: "S1",
        createdAt: "2026-05-11T00:00:00.000Z"
      });
      const result = await handleJoin(
        makeEvent({
          body: JSON.stringify({
            sessionCode: "S1",
            displayName: "Ana",
            skills: ["1", "2", "3"]
          })
        })
      );
      expect(result.statusCode).toBe(200);
      const body = JSON.parse(result.body ?? "{}");
      expect(body.participantId).toMatch(/^[0-9a-f-]{36}$/);
      expect(body.photoUrl).toBe(""); // empty because no objectKey
    });
  });

  describe("wall", () => {
    it("returns empty list when no participants", async () => {
      (ddb.queryParticipants as jest.Mock).mockResolvedValueOnce([]);
      const result = await handleWall(
        makeEvent({
          requestContext: { http: { method: "GET", path: "/wall" } },
          queryStringParameters: { sessionCode: "S1" }
        })
      );
      expect(result.statusCode).toBe(200);
      const body = JSON.parse(result.body ?? "{}");
      expect(body.items).toEqual([]);
    });
  });

  describe("leaderboard", () => {
    it("aggregates skill likes", async () => {
      (ddb.queryParticipants as jest.Mock).mockResolvedValueOnce([
        {
          participantId: "p1",
          displayName: "Ana",
          photoObjectKey: "",
          skills: [
            { skillId: "1", skillName: "Frontend", likeCount: 3 },
            { skillId: "2", skillName: "Backend", likeCount: 1 }
          ],
          totalLikes: 4,
          createdAt: "2026-05-11T00:00:00.000Z"
        },
        {
          participantId: "p2",
          displayName: "Luis",
          photoObjectKey: "",
          skills: [{ skillId: "1", skillName: "Frontend", likeCount: 5 }],
          totalLikes: 5,
          createdAt: "2026-05-11T00:01:00.000Z"
        }
      ]);
      const result = await handleLeaderboard(
        makeEvent({ queryStringParameters: { sessionCode: "S1" } })
      );
      expect(result.statusCode).toBe(200);
      const body = JSON.parse(result.body ?? "{}");
      expect(body.topParticipants[0].displayName).toBe("Luis");
      const frontend = body.topSkills.find((s: any) => s.skillId === "1");
      expect(frontend.totalLikes).toBe(8);
    });
  });

  describe("admin-create", () => {
    it("rejects invalid admin token", async () => {
      const result = await handleAdminCreate(
        makeEvent({ body: JSON.stringify({ adminToken: "wrong", sessionCode: "S1" }) })
      );
      expect(result.statusCode).toBe(401);
    });

    it("creates a new session with valid token", async () => {
      (ddb.getSession as jest.Mock).mockResolvedValueOnce(null);
      const result = await handleAdminCreate(
        makeEvent({
          body: JSON.stringify({ adminToken: "test-admin-token", sessionCode: "S1" })
        })
      );
      expect(result.statusCode).toBe(201);
      const body = JSON.parse(result.body ?? "{}");
      expect(body.sessionCode).toBe("S1");
    });

    it("returns 409 if session already exists", async () => {
      (ddb.getSession as jest.Mock).mockResolvedValueOnce({
        PK: "SESSION#S1",
        SK: "METADATA",
        sessionCode: "S1",
        createdAt: "2026-05-11T00:00:00.000Z"
      });
      const result = await handleAdminCreate(
        makeEvent({
          body: JSON.stringify({ adminToken: "test-admin-token", sessionCode: "S1" })
        })
      );
      expect(result.statusCode).toBe(409);
    });
  });

  describe("admin-delete", () => {
    it("accepts token via Authorization Bearer header", async () => {
      (ddb.batchDeleteSession as jest.Mock).mockResolvedValueOnce(7);
      const result = await handleAdminDelete(
        makeEvent({
          requestContext: { http: { method: "DELETE", path: "/admin/sessions/S1" } },
          headers: { authorization: "Bearer test-admin-token" },
          pathParameters: { code: "S1" }
        })
      );
      expect(result.statusCode).toBe(200);
      const body = JSON.parse(result.body ?? "{}");
      expect(body.itemsDeleted).toBe(7);
    });

    it("rejects invalid token from query param", async () => {
      const result = await handleAdminDelete(
        makeEvent({
          requestContext: { http: { method: "DELETE", path: "/admin/sessions/S1" } },
          queryStringParameters: { adminToken: "nope" },
          pathParameters: { code: "S1" }
        })
      );
      expect(result.statusCode).toBe(401);
    });
  });
});
