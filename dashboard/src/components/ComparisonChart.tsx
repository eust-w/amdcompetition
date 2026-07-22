import { percent } from "../format";
import type { SeedRow } from "../types";

export function ComparisonChart({ rows }: { rows: SeedRow[] }) {
  return (
    <section className="panel comparison-panel" id="runs">
      <div className="panel-heading">
        <div>
          <span className="section-label">Paired deterministic seeds</span>
          <h2>Baseline vs recovery</h2>
        </div>
        <div className="chart-legend" aria-label="Chart legend">
          <span><i className="legend-baseline" />Baseline</span>
          <span><i className="legend-recovery" />Recovery</span>
        </div>
      </div>
      <div className="chart-area" role="img" aria-label="Success rate per seed comparing baseline and recovery">
        <div className="y-axis"><span>100%</span><span>50%</span><span>0%</span></div>
        <div className="bars">
          {rows.map((row) => (
            <div className="bar-group" key={row.seed} title={`Seed ${row.seed}: ${percent(row.baseline_success_rate)} → ${percent(row.recovery_success_rate)}`}>
              <div className="bar-pair">
                <i className="bar baseline" style={{ height: `${row.baseline_success_rate * 100}%` }} />
                <i className="bar recovery" style={{ height: `${row.recovery_success_rate * 100}%` }} />
              </div>
              <span>{row.seed}</span>
            </div>
          ))}
        </div>
      </div>
      <p className="chart-footnote">Every policy sees the same scenario for each seed and episode index.</p>
    </section>
  );
}

