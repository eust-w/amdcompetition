import { CheckCircle2, ShieldCheck } from "lucide-react";
import { integer, percent } from "../format";
import type { Report, ReproducibilityCertificate } from "../types";

type SummaryStripProps = {
  report: Report;
  certificate?: ReproducibilityCertificate;
};

export function SummaryStrip({ report, certificate }: SummaryStripProps) {
  const { metrics, backend_evidence: backend } = report;
  const proven = certificate?.passed === true;
  const status = proven ? "REPRODUCIBLE" : backend.rocm_verified ? "ROCM VERIFIED" : "TRACEABLE RUN";
  const detail = proven
    ? "Two independent runs matched within tolerance"
    : backend.claim_boundary ?? "Artifact digests recorded";

  return (
    <section className="summary-strip" id="overview" aria-label="Evaluation summary">
      <div className="summary-status">
        <span className="section-label">Evidence status</span>
        <div className="status-title">
          {proven ? <CheckCircle2 size={24} /> : <ShieldCheck size={24} />}
          {status}
        </div>
        <p>{detail}</p>
      </div>
      <Metric label="Baseline success" value={percent(metrics.baseline_success_rate)} detail={`${integer(metrics.baseline_successes)} / ${integer(metrics.episodes)}`} />
      <Metric label="Recovery success" value={percent(metrics.recovery_success_rate)} detail={`${integer(metrics.recovery_successes)} / ${integer(metrics.episodes)}`} />
      <Metric label="Failure recovery" value={percent(metrics.failure_recovery_rate)} detail={`${integer(metrics.recovered_failures)} / ${integer(metrics.baseline_failures)}`} />
      <Metric label="Mean retries" value={metrics.mean_retries.toFixed(2)} detail={`Success lift ${percent(metrics.absolute_success_lift)}`} />
    </section>
  );
}

function Metric({ label, value, detail }: { label: string; value: string; detail: string }) {
  return (
    <div className="metric">
      <span className="section-label">{label}</span>
      <strong>{value}</strong>
      <span>{detail}</span>
    </div>
  );
}

