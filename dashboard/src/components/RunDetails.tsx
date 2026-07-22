import { Cpu, Database, GitCommitHorizontal } from "lucide-react";
import { shortHash } from "../format";
import type { Report } from "../types";

export function RunDetails({ report }: { report: Report }) {
  const backend = report.backend_evidence;
  const fields = [
    ["Run ID", report.run_id],
    ["Benchmark", report.benchmark],
    ["Backend", backend.backend],
    ["Engine", backend.engine],
    ["Accelerator", backend.devices?.join(", ") || backend.accelerator],
    ["HIP", backend.hip_version || "not applicable"],
    ["Python", report.runtime.python],
    ["Wall time", `${report.runtime.wall_time_seconds.toFixed(2)} s`],
    ["Git commit", report.git_commit],
    ["Config digest", shortHash(report.config_digest, 18)],
    ["Result digest", shortHash(report.result_digest, 18)],
  ];
  return (
    <section className="panel run-details">
      <div className="panel-heading">
        <div>
          <span className="section-label">Immutable provenance</span>
          <h2>Latest run</h2>
        </div>
        <div className="detail-icons" aria-hidden="true"><Cpu size={17} /><Database size={17} /><GitCommitHorizontal size={17} /></div>
      </div>
      <dl>
        {fields.map(([label, value]) => (
          <div key={label}>
            <dt>{label}</dt>
            <dd title={value}>{value}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

