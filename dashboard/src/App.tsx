import { useCallback, useEffect, useState } from "react";
import { AlertTriangle, RefreshCcw } from "lucide-react";
import { fetchLatest, runEvaluation } from "./api";
import { Artifacts } from "./components/Artifacts";
import { ComparisonChart } from "./components/ComparisonChart";
import { FailureTable } from "./components/FailureTable";
import { Header } from "./components/Header";
import { RecoveryTimeline } from "./components/RecoveryTimeline";
import { RunDetails } from "./components/RunDetails";
import { SummaryStrip } from "./components/SummaryStrip";
import { TrajectoryPreview } from "./components/TrajectoryPreview";
import type { LatestResponse } from "./types";

export default function App() {
  const [data, setData] = useState<LatestResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);

  const load = useCallback(async (signal?: AbortSignal) => {
    try {
      setError(null);
      setData(await fetchLatest(signal));
    } catch (caught) {
      if (!(caught instanceof DOMException && caught.name === "AbortError")) {
        setError(caught instanceof Error ? caught.message : String(caught));
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    void load(controller.signal);
    return () => controller.abort();
  }, [load]);

  async function evaluate() {
    setRunning(true);
    setError(null);
    try {
      setData(await runEvaluation());
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
    } finally {
      setRunning(false);
    }
  }

  const backendLabel = data?.report.backend_evidence.rocm_verified
    ? "ROCm · Radeon"
    : data?.report.backend_evidence.backend ?? "Backend pending";

  return (
    <div className="app-shell">
      <Header backend={backendLabel} running={running} onRun={() => void evaluate()} />
      <main>
        {loading ? <LoadingState /> : null}
        {!loading && error && !data ? <EmptyState error={error} onRetry={() => void load()} /> : null}
        {error && data ? <div className="inline-error"><AlertTriangle size={17} />{error}</div> : null}
        {data ? (
          <>
            <SummaryStrip report={data.report} certificate={data.reproducibility} />
            <div className="primary-grid">
              <ComparisonChart rows={data.report.metrics.per_seed} />
              <RunDetails report={data.report} />
            </div>
            <div className="secondary-grid">
              <FailureTable rows={data.report.metrics.failure_taxonomy} />
              <RecoveryTimeline example={data.report.example_recovery} />
            </div>
            <div className="bottom-grid">
              <Artifacts manifest={data.manifest} />
              <TrajectoryPreview example={data.report.example_recovery} />
            </div>
          </>
        ) : null}
      </main>
      <footer>
        <span>RoboRecover · paired failure-recovery evaluation</span>
        <span>All claims are derived from the active run artifacts.</span>
      </footer>
    </div>
  );
}

function LoadingState() {
  return <div className="loading-state"><span />Loading evaluation evidence…</div>;
}

function EmptyState({ error, onRetry }: { error: string; onRetry: () => void }) {
  return (
    <section className="empty-state">
      <AlertTriangle size={30} />
      <h1>No evaluation artifact yet</h1>
      <p>{error}</p>
      <p>Run <code>roborecover evaluate --backend analytic</code>, then refresh this console.</p>
      <button className="primary-button" type="button" onClick={onRetry}><RefreshCcw size={15} />Refresh</button>
    </section>
  );
}

