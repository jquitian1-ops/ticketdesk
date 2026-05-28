import type { APIGatewayProxyEventV2, APIGatewayProxyStructuredResultV2 } from "aws-lambda";
import { json, error, HttpError, getQuery } from "../http";
import { wallQuerySchema } from "../middleware/validation";
import { queryParticipants } from "../services/dynamodb";
import { getReadUrl } from "../services/s3";
import { logger } from "../middleware/logger";
import type { Participant, WallResponse } from "../types";

export async function handleWall(
  event: APIGatewayProxyEventV2
): Promise<APIGatewayProxyStructuredResultV2> {
  try {
    const parsed = wallQuerySchema.safeParse({
      sessionCode: getQuery(event, "sessionCode"),
      sort: getQuery(event, "sort")
    });
    if (!parsed.success) {
      logger.warn("VALIDATION_FAILED", { route: "wall", issues: parsed.error.issues });
      return error(400, "Validation failed", parsed.error.issues);
    }
    const { sessionCode, sort } = parsed.data;

    const records = await queryParticipants(sessionCode);

    if (sort === "top") {
      records.sort((a, b) => b.totalLikes - a.totalLikes);
    } else {
      records.sort((a, b) => (b.createdAt > a.createdAt ? 1 : -1));
    }

    const items: Participant[] = await Promise.all(
      records.map(async (r) => ({
        participantId: r.participantId,
        displayName: r.displayName,
        photoUrl: await getReadUrl(r.photoObjectKey),
        skills: r.skills,
        totalLikes: r.totalLikes ?? 0,
        createdAt: r.createdAt
      }))
    );

    const response: WallResponse = { items };
    return json(200, response);
  } catch (err) {
    if (err instanceof HttpError) return error(err.statusCode, err.message);
    logger.error("WALL_ERROR", { error: String(err) });
    return error(500, "Internal error");
  }
}
