export const API_BASE = (
  process.env.INCIDENT_MEMORY_API_URL ?? "http://23.21.42.197:8002"
).replace(/\/+$/, "");
