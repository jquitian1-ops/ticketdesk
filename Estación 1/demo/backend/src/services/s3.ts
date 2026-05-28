import { S3Client, GetObjectCommand, PutObjectCommand } from "@aws-sdk/client-s3";
import { getSignedUrl } from "@aws-sdk/s3-request-presigner";

const bucket = (): string => {
  const name = process.env.S3_BUCKET_NAME;
  if (!name) throw new Error("S3_BUCKET_NAME env var is required");
  return name;
};

const client = new S3Client({});
const EXPIRY_SECONDS = 60 * 60; // 1 hour

export async function getUploadUrl(objectKey: string, contentType: string): Promise<string> {
  const cmd = new PutObjectCommand({
    Bucket: bucket(),
    Key: objectKey,
    ContentType: contentType
  });
  return getSignedUrl(client, cmd, { expiresIn: EXPIRY_SECONDS });
}

export async function getReadUrl(objectKey: string): Promise<string> {
  if (!objectKey) return "";
  const cmd = new GetObjectCommand({ Bucket: bucket(), Key: objectKey });
  return getSignedUrl(client, cmd, { expiresIn: EXPIRY_SECONDS });
}
