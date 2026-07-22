import type { LatestResponse } from "./types";

async function parseResponse(response: Response): Promise<LatestResponse> {
  const body = await response.json();
  if (!response.ok) {
    throw new Error(body.error ?? `Request failed with status ${response.status}`);
  }
  return body as LatestResponse;
}

export async function fetchLatest(signal?: AbortSignal): Promise<LatestResponse> {
  return parseResponse(await fetch("/api/latest", { signal, cache: "no-store" }));
}

export async function runEvaluation(): Promise<LatestResponse> {
  const response = await fetch("/api/evaluate", { method: "POST" });
  const body = await response.json();
  if (!response.ok) {
    throw new Error(body.error ?? `Evaluation failed with status ${response.status}`);
  }
  return fetchLatest();
}

