// Troubleshooting #1: Lambda nodejs22.x treats .js as CommonJS by default.
// Bundle with format: 'cjs' to avoid "Cannot use import statement outside a module".
import { build } from "esbuild";

await build({
  entryPoints: ["src/index.ts"],
  bundle: true,
  platform: "node",
  target: "node22",
  format: "cjs",
  outfile: "dist/index.js",
  sourcemap: true,
  minify: false,
  legalComments: "none",
  external: []
});

console.log("Build complete: dist/index.js");
