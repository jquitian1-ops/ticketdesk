import type { APIGatewayProxyEventV2, APIGatewayProxyStructuredResultV2 } from "aws-lambda";
import { json, error, HttpError, getQuery } from "../http";
import { leaderboardQuerySchema } from "../middleware/validation";
import { queryParticipants } from "../services/dynamodb";
import { getReadUrl } from "../services/s3";
import { logger } from "../middleware/logger";
import type { LeaderEntry, LeaderboardResponse, SkillEntry } from "../types";

const TOP_LIMIT = 10;

export async function handleLeaderboard(
  event: APIGatewayProxyEventV2
): Promise<APIGatewayProxyStructuredResultV2> {
  try {
    const parsed = leaderboardQuerySchema.safeParse({
      sessionCode: getQuery(event, "sessionCode")
    });
    if (!parsed.success) {
      logger.warn("VALIDATION_FAILED", { route: "leaderboard", issues: parsed.error.issues });
      return error(400, "Validation failed", parsed.error.issues);
    }
    const { sessionCode } = parsed.data;

    const records = await queryParticipants(sessionCode);

    const sortedParticipants = [...records].sort((a, b) => b.totalLikes - a.totalLikes).slice(0, TOP_LIMIT);
    const topParticipants: LeaderEntry[] = await Promise.all(
      sortedParticipants.map(async (r) => ({
        participantId: r.participantId,
        displayName: r.displayName,
        photoUrl: await getReadUrl(r.photoObjectKey),
        totalLikes: r.totalLikes ?? 0
      }))
    );

    const aggregate = new Map<string, { skillName: string; totalLikes: number }>();
    for (const r of records) {
      for (const s of r.skills) {
        const existing = aggregate.get(s.skillId);
        if (existing) {
          existing.totalLikes += s.likeCount;
        } else {
          aggregate.set(s.skillId, { skillName: s.skillName, totalLikes: s.likeCount });
        }
      }
    }
    const topSkills: SkillEntry[] = Array.from(aggregate.entries())
      .map(([skillId, v]) => ({ skillId, skillName: v.skillName, totalLikes: v.totalLikes }))
      .sort((a, b) => b.totalLikes - a.totalLikes)
      .slice(0, TOP_LIMIT);

    const response: LeaderboardResponse = { topParticipants, topSkills };
    return json(200, response);
  } catch (err) {
    if (err instanceof HttpError) return error(err.statusCode, err.message);
    logger.error("LEADERBOARD_ERROR", { error: String(err) });
    return error(500, "Internal error");
  }
}
