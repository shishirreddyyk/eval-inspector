import { useEffect, useState } from "react";
import { getRun, tagCase } from "../api";
import type { RunDetail as Detail } from "../types";

const TAGS = ["hallucination", "missing-citation", "formatting", "refusal", "other"];

export function RunDetail({ runId }: { runId: string }) {
  const [detail, setDetail] = useState<Detail | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    getRun(runId).then(setDetail).catch((e: Error) => setError(e.message));
  };
  useEffect(load, [runId]);

  if (error) return <p className="err">Could not load {runId}: {error}</p>;
  if (!detail) return <p className="sub">Loading {runId}…</p>;

  const onTag = async (caseId: string, tag: string) => {
    await tagCase(runId, caseId, tag);
    load();
  };

  return (
    <>
      <div className="stat">
        <div><span className="n">{detail.passed}/{detail.total}</span><span className="k">answered cases passing</span></div>
        <div><span className="n">{Math.round((detail.passed / Math.max(detail.total, 1)) * 100)}%</span><span className="k">pass rate</span></div>
        <div><span className="n mono">{detail.model}</span><span className="k">model</span></div>
      </div>

      {detail.unanswered.length > 0 && (
        <div className="warnbox">
          {detail.unanswered.length} case{detail.unanswered.length > 1 ? "s" : ""} in the eval set
          never got an answer in this run: <span className="mono">{detail.unanswered.join(", ")}</span>.
          They are excluded from the pass rate above, which is why the rate alone is not the whole story.
        </div>
      )}

      <div className="card">
        <table>
          <thead>
            <tr><th style={{ width: 90 }}>Verdict</th><th>Case</th><th style={{ width: 210 }}>Tag</th></tr>
          </thead>
          <tbody>
            {detail.cases.map((c) => (
              <tr key={c.case_id}>
                <td><span className={`pill ${c.verdict}`}>{c.verdict}</span></td>
                <td>
                  <strong className="mono">{c.case_id}</strong> — {c.question}
                  <div className="out">{c.output}</div>
                  {c.checks.filter((k) => !k.passed).map((k) => (
                    <div className="why" key={k.kind + k.target}>
                      {k.kind} “{k.target}” — {k.detail}
                    </div>
                  ))}
                  {c.note && <div className="sub" style={{ margin: "4px 0 0" }}>note: {c.note}</div>}
                </td>
                <td>
                  {c.verdict === "fail" ? (
                    <select value={c.tag ?? ""} onChange={(e) => onTag(c.case_id, e.target.value)}>
                      <option value="" disabled>tag this failure…</option>
                      {TAGS.map((t) => <option key={t} value={t}>{t}</option>)}
                    </select>
                  ) : (
                    <span className="sub">—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
