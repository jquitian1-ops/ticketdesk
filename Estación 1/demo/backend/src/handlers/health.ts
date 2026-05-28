import type { APIGatewayProxyEventV2, APIGatewayProxyStructuredResultV2 } from "aws-lambda";
import { json } from "../http";
import { describeTable } from "../services/dynamodb";
import { logger } from "../middleware/logger";
import type { HealthResponse } from "../types";

export async function handleHealth(
  _event: APIGatewayProxyEventV2
): Promise<APIGatewayProxyStructuredResultV2> {
  let dynamodbStatus: "ok" | "error" = "ok";
  try {
    await describeTable();
  } catch (err) {
    dynamodbStatus = "error";
    logger.error("HEALTH_CHECK_FAILED", { error: String(err) });
  }
  const body: HealthResponse = {
    status: dynamodbStatus === "ok" ? "ok" : "degraded",
    dynamodb: dynamodbStatus,
    timestamp: new Date().toISOString()
  };
  return json(200, body);
}
