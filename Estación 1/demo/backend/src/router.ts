import type { APIGatewayProxyEventV2, APIGatewayProxyStructuredResultV2 } from "aws-lambda";
import { getMethod, getPath, error } from "./http";
import { handleHealth } from "./handlers/health";
import { handleUploadUrl } from "./handlers/upload-url";
import { handleJoin } from "./handlers/join";
import { handleWall } from "./handlers/wall";
import { handleLike } from "./handlers/like";
import { handleLeaderboard } from "./handlers/leaderboard";
import { handleAdminCreate } from "./handlers/admin-create";
import { handleAdminDelete } from "./handlers/admin-delete";

type Handler = (event: APIGatewayProxyEventV2) => Promise<APIGatewayProxyStructuredResultV2>;

const STATIC_ROUTES: Record<string, Handler> = {
  "GET /health": handleHealth,
  "POST /upload-url": handleUploadUrl,
  "POST /join": handleJoin,
  "GET /wall": handleWall,
  "POST /like": handleLike,
  "GET /leaderboard": handleLeaderboard,
  "POST /admin/sessions": handleAdminCreate
};

export async function route(event: APIGatewayProxyEventV2): Promise<APIGatewayProxyStructuredResultV2> {
  const method = getMethod(event);
  const path = getPath(event);
  const key = `${method} ${path}`;

  const staticHandler = STATIC_ROUTES[key];
  if (staticHandler) return staticHandler(event);

  if (method === "DELETE" && /^\/admin\/sessions\/[^/]+$/.test(path)) {
    return handleAdminDelete(event);
  }

  return error(404, `Route not found: ${key}`);
}
