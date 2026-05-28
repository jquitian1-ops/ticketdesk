import type {
  APIGatewayProxyEventV2,
  APIGatewayProxyStructuredResultV2,
  Context
} from "aws-lambda";
import { initOtel } from "./middleware/otel";
import { route } from "./router";
import { error, getRouteKey } from "./http";
import { logger } from "./middleware/logger";

// Initialize OTel at module load (cold start). No-op if NEW_RELIC_LICENSE_KEY is missing.
initOtel();

export async function handler(
  event: APIGatewayProxyEventV2,
  context: Context
): Promise<APIGatewayProxyStructuredResultV2> {
  const start = Date.now();
  const routeKey = getRouteKey(event);
  const traceId = context.awsRequestId;
  try {
    const result = await route(event);
    logger.info("REQUEST_COMPLETED", {
      routeKey,
      statusCode: result.statusCode,
      durationMs: Date.now() - start,
      traceId
    });
    return result;
  } catch (err) {
    logger.error("UNHANDLED_ERROR", {
      routeKey,
      error: String(err),
      stack: (err as Error).stack,
      traceId
    });
    return error(500, "Internal error");
  }
}
