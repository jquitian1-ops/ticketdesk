import { randomBytes } from "node:crypto";
import type { APIGatewayProxyEventV2, APIGatewayProxyStructuredResultV2 } from "aws-lambda";
import { parseBody, json, error, HttpError } from "../http";
import { uploadUrlSchema } from "../middleware/validation";
import { getUploadUrl } from "../services/s3";
import { logger } from "../middleware/logger";
import type { UploadUrlResponse } from "../types";

export async function handleUploadUrl(
  event: APIGatewayProxyEventV2
): Promise<APIGatewayProxyStructuredResultV2> {
  try {
    const body = parseBody(event);
    const parsed = uploadUrlSchema.safeParse(body);
    if (!parsed.success) {
      logger.warn("VALIDATION_FAILED", { route: "upload-url", issues: parsed.error.issues });
      return error(400, "Validation failed", parsed.error.issues);
    }
    const { sessionCode, contentType } = parsed.data;
    const ext = contentType === "image/png" ? "png" : contentType === "image/webp" ? "webp" : "jpg";
    const objectKey = `${sessionCode}/${randomBytes(12).toString("hex")}.${ext}`;
    const uploadUrl = await getUploadUrl(objectKey, contentType);
    const response: UploadUrlResponse = { uploadUrl, objectKey };
    return json(200, response);
  } catch (err) {
    if (err instanceof HttpError) return error(err.statusCode, err.message);
    logger.error("UPLOAD_URL_ERROR", { error: String(err) });
    return error(500, "Internal error");
  }
}
