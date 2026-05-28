import { NodeSDK } from "@opentelemetry/sdk-node";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-http";
import { Resource } from "@opentelemetry/resources";
import { SemanticResourceAttributes } from "@opentelemetry/semantic-conventions";
import { HttpInstrumentation } from "@opentelemetry/instrumentation-http";
import { AwsInstrumentation } from "@opentelemetry/instrumentation-aws-sdk";

let started = false;
let sdk: NodeSDK | null = null;

export function initOtel(): void {
  if (started) return;
  const licenseKey = process.env.NEW_RELIC_LICENSE_KEY;
  if (!licenseKey) {
    started = true;
    return;
  }

  const exporter = new OTLPTraceExporter({
    url: "https://otlp.nr-data.net:4318/v1/traces",
    headers: { "api-key": licenseKey }
  });

  sdk = new NodeSDK({
    resource: new Resource({
      [SemanticResourceAttributes.SERVICE_NAME]: "skillwall-backend",
      [SemanticResourceAttributes.DEPLOYMENT_ENVIRONMENT]: process.env.ENVIRONMENT ?? "dev"
    }),
    traceExporter: exporter,
    instrumentations: [new HttpInstrumentation(), new AwsInstrumentation()]
  });

  try {
    sdk.start();
    started = true;
  } catch (err) {
    console.warn(JSON.stringify({ level: "warn", event: "OTEL_INIT_FAILED", error: String(err) }));
    started = true;
  }
}

export async function shutdownOtel(): Promise<void> {
  if (sdk) {
    try {
      await sdk.shutdown();
    } catch {
      // ignore
    }
  }
}
