import type { APIGatewayProxyEventV2, APIGatewayProxyStructuredResultV2 } from "aws-lambda";
import { parseBody, json, error, HttpError } from "../http";
import { likeSchema } from "../middleware/validation";
import { getParticipant, incrementSkillLike } from "../services/dynamodb";
import { logger } from "../middleware/logger";
import type { LikeResponse } from "../types";

export async function handleLike(
  event: APIGatewayProxyEventV2
): Promise<APIGatewayProxyStructuredResultV2> {
  try {
    const body = parseBody(event);
    const parsed = likeSchema.safeParse(body);
    if (!parsed.success) {
      logger.warn("VALIDATION_FAILED", { route: "like", issues: parsed.error.issues });
      return error(400, "Validation failed", parsed.error.issues);
    }
    const { sessionCode, voterId, targetParticipantId, skillId } = parsed.data;

    // No self-vote
    if (voterId === targetParticipantId) {
      return error(400, "Self-vote is not allowed");
    }

    // Voter must be a registered participant
    const voter = await getParticipant(sessionCode, voterId);
    if (!voter) {
      return error(403, "Voter is not a registered participant");
    }

    // Target must exist and have this skill
    const target = await getParticipant(sessionCode, targetParticipantId);
    if (!target) {
      return error(404, "Target participant not found");
    }
    const skillIndex = target.skills.findIndex((s) => s.skillId === skillId);
    if (skillIndex < 0) {
      return error(400, "Target has not registered this skill");
    }

    const currentCount = target.skills[skillIndex].likeCount;

    const { alreadyVoted } = await incrementSkillLike({
      sessionCode,
      voterId,
      targetParticipantId,
      skillId,
      skillIndex
    });

    if (alreadyVoted) {
      logger.info("IDEMPOTENT_LIKE", { sessionCode, voterId, targetParticipantId, skillId });
      const response: LikeResponse = { likeCount: currentCount };
      return json(200, response);
    }

    logger.info("LIKE_CAST", { sessionCode, voterId, targetParticipantId, skillId });
    const response: LikeResponse = { likeCount: currentCount + 1 };
    return json(200, response);
  } catch (err) {
    if (err instanceof HttpError) return error(err.statusCode, err.message);
    logger.error("LIKE_ERROR", { error: String(err) });
    return error(500, "Internal error");
  }
}
