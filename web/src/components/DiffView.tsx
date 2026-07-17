import { useEffect, useState } from "react";
import { getDiff } from "../api";
import type { DiffResult, DiffStatus, RunSummary } from "../types";

const SHOWN: DiffStatus[] = ["regressed", "dropped", "still_failing", "fixed", "new"];

export function DiffView({ runs }: { runs: RunSummary[] }) {
  const [a, setA] = useState(runs[runs.length - 1]?.run_id ?? "");
  const [b, setB] = useState(runs[0]?.run_id ?? "");
  const [diff, setDiff] = useState<DiffResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!a || !b) return;
    setError(null);
    getDiff(a, b).then(setDiff).catch((e: Error) => setError(e.message));
  }, [a, b]);

  const picker = (value: string, onChange: (v: string) => void, label: string) => (
    <label className="sub">
      {label}{" "}
      <select value={value} onChange={(e) => onChange(e.target.value)}>
        {runs.map((r) => <option key={r.run_id} value={r.run_id}>{r.run_id}</option>)}
      </select>
    </label>
  );

  return (
    <>
      <div className="bar">
        {picker(a, setA, "baseline")}
        {picker(b, setB, "candidate")}
      </div>

      {error && <p className="err">{error}</p>}
      {!diff ? <p className="sub">Loading diff…</p> : (
        <>
          <div className="stat">
            {SHOWN.map((s) => (
              <div key={s}>
                <span className="n">{diff.counts[s] ?? 0}</span>
                <span className="k">{s.replace("_", " ")}</span>
              </div>
            ))}
          </div>

          <div className="card">
            <table>
              <thead>
                <tr><th style={{ width: 110 }}>Status</th><th>Case</th><th>Baseline</th><th>Candidate</th></tr>
              </thead>
              <tbody>
                {diff.cases
                  .filter((c) => c.status !== "still_passing")
                  .map((c) => (
                    <tr key={c.case_id}>
                      <td><span className={`pill ${c.status}`}>{c.status.replace("_", " ")}</span></td>
                      <td><strong className="mono">{c.case_id}</strong><div className="sub">{c.question}</div></td>
                      <td>
                        <div className="out">{c.a_output ?? <em>not answered</em>}</div>
                        {c.a_failed.map((f) => <div className="why" key={f}>failed: {f}</div>)}
                      </td>
                      <td>
                        <div className="out">{c.b_output ?? <em>not answered</em>}</div>
                        {c.b_failed.map((f) => <div className="why" key={f}>failed: {f}</div>)}
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
          <p className="sub" style={{ marginTop: 10 }}>
            Cases that pass in both runs are hidden — this screen is for what moved.
          </p>
        </>
      )}
    </>
  );
}
