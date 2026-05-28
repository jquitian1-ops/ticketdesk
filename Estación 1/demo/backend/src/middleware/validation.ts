import { z } from "zod";
import { SKILL_ID_SET } from "../constants/skills";

const sessionCodeSchema = z
  .string()
  .min(1)
  .max(64)
  .regex(/^[A-Za-z0-9_-]{1,64}$/, "sessionCode must match ^[A-Za-z0-9_-]{1,64}$");

const displayNameSchema = z.string().trim().min(1).max(200);

const participantIdSchema = z
  .string()
  .regex(/^[0-9a-f-]{36}$/, "participantId must be a UUID");

const skillIdSchema = z
  .string()
  .refine((id) => SKILL_ID_SET.has(id), { message: "Unknown skillId" });

const skillsSchema = z
  .array(skillIdSchema)
  .min(3, "Must select at least 3 skills")
  .max(5, "Must select at most 5 skills");

// Troubleshooting #13: photoObjectKey optional, empty string allowed for default avatar.
const photoObjectKeySchema = z
  .string()
  .max(512)
  .regex(/^[A-Za-z0-9/_.-]*$/, "photoObjectKey contains invalid characters")
  .refine((s) => !s.includes(".."), { message: "photoObjectKey must not contain '..'" });

const contentTypeSchema = z.enum(["image/jpeg", "image/png", "image/webp"]);

export const uploadUrlSchema = z.object({
  sessionCode: sessionCodeSchema,
  contentType: contentTypeSchema
});

export const joinSchema = z.object({
  sessionCode: sessionCodeSchema,
  displayName: displayNameSchema,
  skills: skillsSchema,
  photoObjectKey: photoObjectKeySchema.optional().default("")
});

export const wallQuerySchema = z.object({
  sessionCode: sessionCodeSchema,
  sort: z.enum(["new", "top"]).optional().default("new")
});

export const likeSchema = z.object({
  sessionCode: sessionCodeSchema,
  voterId: participantIdSchema,
  targetParticipantId: participantIdSchema,
  skillId: skillIdSchema
});

export const leaderboardQuerySchema = z.object({
  sessionCode: sessionCodeSchema
});

export const adminCreateSchema = z.object({
  adminToken: z.string().min(1),
  sessionCode: sessionCodeSchema
});

export const adminDeleteSchema = z.object({
  adminToken: z.string().min(1)
});

export type UploadUrlInput = z.infer<typeof uploadUrlSchema>;
export type JoinInput = z.infer<typeof joinSchema>;
export type WallQuery = z.infer<typeof wallQuerySchema>;
export type LikeInput = z.infer<typeof likeSchema>;
export type LeaderboardQuery = z.infer<typeof leaderboardQuerySchema>;
export type AdminCreateInput = z.infer<typeof adminCreateSchema>;
export type AdminDeleteInput = z.infer<typeof adminDeleteSchema>;
