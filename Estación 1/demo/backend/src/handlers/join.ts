import { randomUUID } from "node:crypto";
import type { APIGatewayProxyEventV2, APIGatewayProxyStructuredResultV2 } from "aws-lambda";
import { parseBody, json, error, HttpError } from "../http";
import { joinSchema } from "../middleware/validation";
import { getSession, putParticipant } from "../services/dynamodb";
import { getReadUrl } from "../services/s3";
import { getSkillName } from "../constants/skills";
import { logger } from "../middleware/logger";
import type { JoinResponse, ParticipantRecord, Skill } from "../types";

export async function handleJoin(
  event: APIGatewayProxyEventV2
): Promise<APIGatewayProxyStructuredResultV2> {
  try {
    const body = parseBody(event);
    const parsed = joinSchema.safeParse(body);
    if (!parsed.success) {
      logger.warn("VALIDATION_FAILED", { route: "join", issues: parsed.error.issues });
      return error(400, "Validation failed", parsed.error.issues);
    }
    const { sessionCode, displayName, skills, photoObjectKey } = parsed.data;

    // Troubleshooting #32: session must be seeded via /admin/sessions before /join works.
    const session = await getSession(sessionCode);
    if (!session) {
      return error(404, "Session not found");
    }

    const participantId = randomUUID();
    const skillRecords: Skill[] = skills.map((skillId) => ({
      skillId,
      skillName: getSkillName(skillId) ?? "Unknown",
      likeCount: 0
    }));

    const record: ParticipantRecord = {
      PK: `SESSION#${sessionCode}`,
      SK: `PARTICIPANT#${participantId}`,
      participantId,
      sessionCode,
      displayName: displayName.trim(),
      photoObjectKey: photoObjectKey ?? "",
      skills: skillRecords,
      totalLikes: 0,
      createdAt: new Date().toISOString()
    };

    await putParticipant(record);

    const photoUrl = await getReadUrl(record.photoObjectKey);

    logger.info("JOIN_CREATED", { sessionCode, participantId });

    const response: JoinResponse = {
      participantId,
      displayName: record.displayName,
      photoUrl,
      skills: skillRecords
    };
    return json(200, response);
  } catch (err) {
    if (err instanceof HttpError) return error(err.statusCode, err.message);
    logger.error("JOIN_ERROR", { error: String(err) });
    return error(500, "Internal error");
  }
}
