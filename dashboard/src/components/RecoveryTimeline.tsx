import { titleCase } from "../format";
import type { AttemptState, ExampleRecovery } from "../types";

export function RecoveryTimeline({ example }: { example: ExampleRecovery | null }) {
  const attempts = example?.recovery.attempts ?? [];
  const firstAttempt = attempts[0];
  const lastAttempt = attempts.at(-1);
  const initialStates = firstAttempt?.states.slice(0, 4) ?? [];
  const retryState: AttemptState[] = attempts.length > 1
    ? [{ state: "retry", t_ms: firstAttempt?.simulated_latency_ms ?? 0, status: "ok" }]
    : [];
  const terminalState = attempts.length > 1 && lastAttempt
    ? lastAttempt.states.slice(-1)
    : [];
  const states = [...initialStates, ...retryState, ...terminalState];
  return (
    <section className="panel timeline-panel">
      <div className="panel-heading">
        <div>
          <span className="section-label">Example episode · {example?.episode_id ?? "none"}</span>
          <h2>Recovery state machine</h2>
        </div>
      </div>
      {states.length > 0 ? (
        <div className="timeline">
          {states.map((state, index) => (
            <div className={`timeline-step ${state.status}`} key={`${state.state}-${state.t_ms}-${index}`}>
              <span className="timeline-node" />
              <strong>{titleCase(state.state)}</strong>
              <small>{(state.t_ms / 1000).toFixed(3)} s</small>
              <span>{state.failure ? titleCase(state.failure) : state.status === "ok" ? "Verified" : "Branch"}</span>
            </div>
          ))}
        </div>
      ) : <p className="empty-copy">No recovery episode is available in this run.</p>}
    </section>
  );
}
