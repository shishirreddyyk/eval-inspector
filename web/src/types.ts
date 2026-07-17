export type Verdict = "pass" | "fail";

export type DiffStatus =
  | "regressed"
  | "dropped"
  | "still_failing"
  | "fixed"
  | "new"
  | "still_passing";

export interface RunSummary {
  run_id: string;
  model: string;
  created_at: string;
  total: number;
  passed: number;
  pass_rate: number;
}

export interface Check {
  kind: string;
  target: string;
  passed: boolean;
  detail: string;
}

export interface CaseResult {
  case_id: string;
  question: string;
  output: string;
  verdict: Verdict;
  checks: Check[];
  latency_ms: number | null;
  tag: string | null;
  note: string;
}

export interface RunDetail {
  run_id: string;
  model: string;
  created_at: string;
  total: number;
  passed: number;
  unanswered: string[];
  cases: CaseResult[];
}

export interface CaseDiff {
  case_id: string;
  question: string;
  status: DiffStatus;
  a_verdict: Verdict | null;
  b_verdict: Verdict | null;
  a_output: string | null;
  b_output: string | null;
  a_failed: string[];
  b_failed: string[];
}

export interface DiffResult {
  a: string;
  b: string;
  counts: Record<DiffStatus, number>;
  cases: CaseDiff[];
}
