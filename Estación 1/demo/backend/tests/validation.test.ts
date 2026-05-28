import {
  uploadUrlSchema,
  joinSchema,
  wallQuerySchema,
  likeSchema,
  leaderboardQuerySchema,
  adminCreateSchema
} from "../src/middleware/validation";

describe("validation schemas", () => {
  describe("uploadUrlSchema", () => {
    it("accepts valid input", () => {
      const r = uploadUrlSchema.safeParse({ sessionCode: "LATAM2026", contentType: "image/jpeg" });
      expect(r.success).toBe(true);
    });
    it("rejects unsupported contentType", () => {
      const r = uploadUrlSchema.safeParse({ sessionCode: "LATAM2026", contentType: "image/gif" });
      expect(r.success).toBe(false);
    });
    it("rejects invalid sessionCode characters", () => {
      const r = uploadUrlSchema.safeParse({ sessionCode: "LATAM 2026!", contentType: "image/jpeg" });
      expect(r.success).toBe(false);
    });
  });

  describe("joinSchema (troubleshooting #13)", () => {
    it("accepts missing photoObjectKey (default empty)", () => {
      const r = joinSchema.safeParse({
        sessionCode: "S1",
        displayName: "Ana",
        skills: ["1", "2", "3"]
      });
      expect(r.success).toBe(true);
      if (r.success) expect(r.data.photoObjectKey).toBe("");
    });
    it("accepts explicit empty photoObjectKey", () => {
      const r = joinSchema.safeParse({
        sessionCode: "S1",
        displayName: "Ana",
        skills: ["1", "2", "3"],
        photoObjectKey: ""
      });
      expect(r.success).toBe(true);
    });
    it("rejects path traversal in photoObjectKey", () => {
      const r = joinSchema.safeParse({
        sessionCode: "S1",
        displayName: "Ana",
        skills: ["1", "2", "3"],
        photoObjectKey: "S1/../etc/passwd"
      });
      expect(r.success).toBe(false);
    });
    it("rejects empty displayName", () => {
      const r = joinSchema.safeParse({
        sessionCode: "S1",
        displayName: "",
        skills: ["1", "2", "3"]
      });
      expect(r.success).toBe(false);
    });
    it("rejects < 3 skills", () => {
      const r = joinSchema.safeParse({
        sessionCode: "S1",
        displayName: "Ana",
        skills: ["1", "2"]
      });
      expect(r.success).toBe(false);
    });
    it("rejects > 5 skills", () => {
      const r = joinSchema.safeParse({
        sessionCode: "S1",
        displayName: "Ana",
        skills: ["1", "2", "3", "4", "5", "6"]
      });
      expect(r.success).toBe(false);
    });
    it("rejects unknown skillId", () => {
      const r = joinSchema.safeParse({
        sessionCode: "S1",
        displayName: "Ana",
        skills: ["1", "99", "3"]
      });
      expect(r.success).toBe(false);
    });
  });

  describe("wallQuerySchema", () => {
    it("defaults sort to 'new'", () => {
      const r = wallQuerySchema.safeParse({ sessionCode: "S1" });
      expect(r.success).toBe(true);
      if (r.success) expect(r.data.sort).toBe("new");
    });
    it("accepts sort=top", () => {
      const r = wallQuerySchema.safeParse({ sessionCode: "S1", sort: "top" });
      expect(r.success).toBe(true);
    });
    it("rejects invalid sort", () => {
      const r = wallQuerySchema.safeParse({ sessionCode: "S1", sort: "random" });
      expect(r.success).toBe(false);
    });
  });

  describe("likeSchema", () => {
    const valid = {
      sessionCode: "S1",
      voterId: "11111111-1111-1111-1111-111111111111",
      targetParticipantId: "22222222-2222-2222-2222-222222222222",
      skillId: "1"
    };
    it("accepts valid input", () => {
      const r = likeSchema.safeParse(valid);
      expect(r.success).toBe(true);
    });
    it("rejects non-UUID voterId", () => {
      const r = likeSchema.safeParse({ ...valid, voterId: "not-a-uuid" });
      expect(r.success).toBe(false);
    });
    it("rejects unknown skill", () => {
      const r = likeSchema.safeParse({ ...valid, skillId: "999" });
      expect(r.success).toBe(false);
    });
  });

  describe("leaderboardQuerySchema", () => {
    it("requires sessionCode", () => {
      const r = leaderboardQuerySchema.safeParse({});
      expect(r.success).toBe(false);
    });
  });

  describe("adminCreateSchema", () => {
    it("requires adminToken", () => {
      const r = adminCreateSchema.safeParse({ sessionCode: "S1" });
      expect(r.success).toBe(false);
    });
  });
});
