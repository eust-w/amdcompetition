import type { ExampleRecovery } from "../types";

export function TrajectoryPreview({ example }: { example: ExampleRecovery | null }) {
  const attempts = example?.recovery.attempts ?? [];
  const recovered = example?.recovery.success ?? false;
  return (
    <section className="panel trajectory-panel">
      <div className="panel-heading">
        <div>
          <span className="section-label">Data-derived episode trace</span>
          <h2>Grasp recovery preview</h2>
        </div>
      </div>
      <div className="trajectory-stage" role="img" aria-label="Data-derived robot grasp trajectory">
        <svg viewBox="0 0 620 260" aria-hidden="true">
          <path className="surface-line" d="M32 218H588" />
          <path className="robot-base" d="M78 218v-36h52v36M104 182l42-56 42 22 58-76" />
          <circle className="joint" cx="104" cy="182" r="9" />
          <circle className="joint" cx="146" cy="126" r="9" />
          <circle className="joint" cx="188" cy="148" r="9" />
          <path className="gripper" d="M246 72l24 12m-21-18 7 27m4-16 19-8" />
          <rect className={recovered ? "target recovered" : "target"} x="448" y="178" width="42" height="40" rx="3" />
          <path className="attempt-path first" d="M270 84C338 82 377 103 424 155" />
          {attempts.length > 1 ? <path className="attempt-path retry" d="M270 84C352 62 434 96 468 176" /> : null}
        </svg>
        <div className="trajectory-key">
          <span><i className="first" />Initial attempt</span>
          <span><i className="retry" />Recovery correction</span>
        </div>
      </div>
      <dl className="trajectory-stats">
        <div><dt>Injected fault</dt><dd>{example?.scenario.injected_failure ?? "n/a"}</dd></div>
        <div><dt>Attempts</dt><dd>{attempts.length || 0}</dd></div>
        <div><dt>Outcome</dt><dd className={recovered ? "success-text" : "failure-text"}>{recovered ? "Recovered" : "Failed"}</dd></div>
      </dl>
    </section>
  );
}

