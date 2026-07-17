import { useEffect, useState } from "react";
import { listRuns } from "./api";
import { RunDetail } from "./components/RunDetail";
import { DiffView } from "./components/DiffView";
import type { RunSummary } from "./types";

type Tab = { kind: "run"; runId: string } | { kind: "diff" };

export default function App() {
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [tab, setTab] = useState<Tab | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listRuns()
      .then((rs) => {
        setRuns(rs);
        const first = rs[0];
        if (first) setTab({ kind: "run", runId: first.run_id });
      })
      .catch((e: Error) => setError(e.message));
  }, []);

  if (error) return <div className="wrap"><p className="err">API unreachable: {error}</p></div>;

  return (
    <div className="wrap">
      <h1>eval-inspector</h1>
      <p className="sub">Model outputs, graded case by case, and what changed between runs.</p>

      <div className="bar">
        {runs.map((r) => (
          <button
            key={r.run_id}
            aria-pressed={tab?.kind === "run" && tab.runId === r.run_id}
            onClick={() => setTab({ kind: "run", runId: r.run_id })}
          >
            {r.model} · {Math.round(r.pass_rate * 100)}%
          </button>
        ))}
        {runs.length >= 2 && (
          <button aria-pressed={tab?.kind === "diff"} onClick={() => setTab({ kind: "diff" })}>
            compare runs
          </button>
        )}
      </div>

      {tab?.kind === "run" && <RunDetail runId={tab.runId} />}
      {tab?.kind === "diff" && <DiffView runs={runs} />}
    </div>
  );
}
