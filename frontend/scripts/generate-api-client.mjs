import { readFile, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";

const scriptDirectory = new URL(".", import.meta.url);
const openApiPath = new URL("../../backend/openapi.json", scriptDirectory);
const outputPath = new URL("../src/api/generated.ts", scriptDirectory);
const contract = JSON.parse(await readFile(openApiPath, "utf8"));

if (!contract.paths?.["/api/v1/cards/random"]?.get) {
  throw new Error("The OpenAPI contract lacks GET /api/v1/cards/random.");
}

const schemas = contract.components?.schemas;
if (!schemas || typeof schemas !== "object") {
  throw new Error("The OpenAPI contract lacks component schemas.");
}

const output = `/* This file is generated from backend/openapi.json. Do not edit manually. */

${Object.entries(schemas)
  .map(([name, schema]) => `export type ${name} = ${toType(schema)};`)
  .join("\n\n")}

export type Card = CardResponse;

export async function getRandomCards(
  baseUrl: string,
  signal?: AbortSignal,
): Promise<RandomCardsResponse> {
  const response = await fetch(baseUrl + "/api/v1/cards/random", { signal });
  if (!response.ok) {
    const detail = (await response.json().catch(() => undefined)) as ApiError | undefined;
    throw new ApiRequestError(response.status, detail);
  }
  return (await response.json()) as RandomCardsResponse;
}

export class ApiRequestError extends Error {
  public constructor(
    public readonly status: number,
    public readonly detail: ApiError | undefined,
  ) {
    super(detail?.message ?? "API request failed with status " + status + ".");
  }
}
`;

await writeFile(outputPath, output, "utf8");
console.log(`Generated ${fileURLToPath(outputPath)}`);

function toType(schema) {
  if (schema.$ref) {
    return schema.$ref.split("/").at(-1);
  }
  if (schema.const !== undefined) {
    return JSON.stringify(schema.const);
  }
  if (schema.enum) {
    return schema.enum.map((value) => JSON.stringify(value)).join(" | ");
  }
  if (schema.anyOf) {
    return schema.anyOf.map(toType).join(" | ");
  }
  if (schema.type === "array") {
    return `Array<${toType(schema.items)}>`;
  }
  if (schema.type === "object" || schema.properties) {
    const required = new Set(schema.required ?? []);
    const properties = Object.entries(schema.properties ?? {})
      .map(([name, property]) => `  ${JSON.stringify(name)}${required.has(name) ? "" : "?"}: ${toType(property)};`)
      .join("\n");
    return `{\n${properties}\n}`;
  }
  return {
    string: "string",
    integer: "number",
    number: "number",
    boolean: "boolean",
    null: "null",
  }[schema.type] ?? "unknown";
}
