import { integer, percent, titleCase } from "../format";
import type { FailureRow } from "../types";

export function FailureTable({ rows }: { rows: FailureRow[] }) {
  const failureRows = rows.filter((row) => row.failure_type !== "none");
  return (
    <section className="panel table-panel" id="failures">
      <div className="panel-heading">
        <div>
          <span className="section-label">Aggregated across paired trials</span>
          <h2>Failure taxonomy</h2>
        </div>
      </div>
      <div className="table-scroll">
        <table>
          <thead><tr><th>Failure type</th><th>Injected</th><th>Failed</th><th>Detected</th><th>Recovered</th><th>Recovery rate</th><th>Latency</th></tr></thead>
          <tbody>
            {failureRows.map((row) => (
              <tr key={row.failure_type}>
                <td>{titleCase(row.failure_type)}</td>
                <td>{integer(row.injected)}</td>
                <td>{integer(row.baseline_failed)}</td>
                <td>{integer(row.detected)}</td>
                <td>{integer(row.recovered)}</td>
                <td className="accent-cell">{percent(row.recovery_rate)}</td>
                <td>{row.mean_recovery_latency_ms.toFixed(0)} ms</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
