// Troubleshooting #7: CommonJS config (.cjs) avoids Jest+Node 22 dynamic-import issues.
// Troubleshooting #8: setupFiles runs BEFORE module imports, so process.env values
// are visible when service singletons read them at import time.
module.exports = {
  preset: "ts-jest",
  testEnvironment: "node",
  roots: ["<rootDir>/tests"],
  testMatch: ["**/*.test.ts"],
  setupFiles: ["<rootDir>/tests/setup.ts"],
  moduleFileExtensions: ["ts", "js", "json"],
  clearMocks: true,
  verbose: false,
  transform: {
    "^.+\\.ts$": ["ts-jest", { tsconfig: { module: "CommonJS", target: "ES2022", esModuleInterop: true, strict: true } }]
  }
};
