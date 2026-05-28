// Troubleshooting #8: Set env vars BEFORE any handler module is imported,
// so that singletons reading process.env at import time see the right values.
process.env.DYNAMODB_TABLE_NAME = "skillwall-test-participants";
process.env.S3_BUCKET_NAME = "skillwall-test-photos";
process.env.ADMIN_TOKEN = "test-admin-token";
process.env.NEW_RELIC_LICENSE_KEY = ""; // disable OTel in tests
process.env.AWS_REGION = "us-east-1";
process.env.AWS_ACCESS_KEY_ID = "TEST";
process.env.AWS_SECRET_ACCESS_KEY = "TEST";
