import type { DiffResult, RunDetail, RunSummary } from "./types";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`${path} -> ${res.status}`);
  return (await res.json()) as T;
}

export const listRuns = () => get<{ runs: RunSummary[] }>("/api/runs").then((r) => r.runs);

export const getRun = (id: string) => get<RunDetail>(`/api/runs/${encodeURIComponent(id)}`);

export const getDiff = (a: string, b: string) =>
  get<DiffResult>(`/api/diff?a=${encodeURIComponent(a)}&b=${encodeURIComponent(b)}`);

export async function tagCase(
  run_id: string,
  case_id: string,
  tag: string,
  note = "",
): Promise<void> {
  const res = await fetch("/api/tags", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ run_id, case_id, tag, note }),
  });
  if (!res.ok) throw new Error(`tag failed: ${res.status}`);
}
