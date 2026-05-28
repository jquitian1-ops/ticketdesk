import type { APIGatewayProxyEventV2, APIGatewayProxyStructuredResultV2 } from "aws-lambda";
import { parseBody, json, error, HttpError, getHeader, getQuery, getPath } from "../http";
import { batchDeleteSession } from "../services/dynamodb";
import { logger } from "../middleware/logger";

function extractAdminToken(event: APIGatewayProxyEventV2): string | undefined {
  try {
    const body = parseBody<{ adminToken?: string }>(event);
    if (body && typeof body.adminToken === "string" && body.adminToken.length > 0) {
      return body.adminToken;
    }
  } catch {
    // Empty / invalid body is OK for DELETE; fall through.
  }
  const headerToken = getHeader(event, "admintoken");
  if (headerToken) return headerToken;
  const auth = getHeader(event, "authorization");
  if (auth && auth.toLowerCase().startsWith("bearer ")) {
    return auth.slice(7).trim();
  }
  return getQuery(event, "adminToken");
}

function extractSessionCode(event: APIGatewayProxyEventV2): string | undefined {
  if (event.pathParameters?.code) return event.pathParameters.code;
  const path = getPath(event);
  const match = path.match(/^\/admin\/sessions\/([^/]+)$/);
  return match?.[1];
}

export async function handleAdminDelete(
  event: APIGatewayProxyEventV2
): Promise<APIGatewayProxyStructuredResultV2> {
  try {
    const expected = process.env.ADMIN_TOKEN;
    const token = extractAdminToken(event);
    if (!expected || token !== expected) {
      return error(401, "Invalid admin token");
    }

    const sessionCode = extractSessionCode(event);
    if (!sessionCode) {
      return error(400, "sessionCode is required in path");
    }

    const deleted = await batchDeleteSession(sessionCode);
    logger.info("SESSION_DELETED", { sessionCode, itemsDeleted: deleted });
    return json(200, { ok: true, sessionCode, itemsDeleted: deleted });
  } catch (err) {
    if (err instanceof HttpError) return error(err.statusCode, err.message);
    logger.error("ADMIN_DELETE_ERROR", { error: String(err) });
    return error(500, "Internal error");
  }
}
