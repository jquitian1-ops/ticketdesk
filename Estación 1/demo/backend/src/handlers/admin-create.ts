import type { APIGatewayProxyEventV2, APIGatewayProxyStructuredResultV2 } from "aws-lambda";
import { parseBody, json, error, HttpError } from "../http";
import { adminCreateSchema } from "../middleware/validation";
import { putSession, getSession } from "../services/dynamodb";
import { logger } from "../middleware/logger";

export async function handleAdminCreate(
  event: APIGatewayProxyEventV2
): Promise<APIGatewayProxyStructuredResultV2> {
  try {
    const body = parseBody(event);
    const parsed = adminCreateSchema.safeParse(body);
    if (!parsed.success) {
      logger.warn("VALIDATION_FAILED", { route: "admin-create", issues: parsed.error.issues });
      return error(400, "Validation failed", parsed.error.issues);
    }
    const expected = process.env.ADMIN_TOKEN;
    if (!expected || parsed.data.adminToken !== expected) {
      return error(401, "Invalid admin token");
    }

    const existing = await getSession(parsed.data.sessionCode);
    if (existing) {
      return error(409, "Session already exists");
    }

    const record = await putSession(parsed.data.sessionCode);
    logger.info("SESSION_CREATED", { sessionCode: parsed.data.sessionCode });
    return json(201, { sessionCode: record.sessionCode, createdAt: record.createdAt });
  } catch (err) {
    if (err instanceof HttpError) return error(err.statusCode, err.message);
    logger.error("ADMIN_CREATE_ERROR", { error: String(err) });
    return error(500, "Internal error");
  }
}
