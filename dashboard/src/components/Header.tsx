import { Activity, Play } from "lucide-react";

type HeaderProps = {
  backend: string;
  running: boolean;
  onRun: () => void;
};

const NAV_ITEMS = ["Overview", "Runs", "Failures", "Artifacts"] as const;

export function Header({ backend, running, onRun }: HeaderProps) {
  function scrollTo(label: (typeof NAV_ITEMS)[number]) {
    const target = document.getElementById(label.toLowerCase());
    target?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  return (
    <header className="app-header">
      <button className="brand" type="button" onClick={() => scrollTo("Overview")}>
        <span className="brand-mark" aria-hidden="true">
          <Activity size={21} strokeWidth={1.8} />
        </span>
        RoboRecover
      </button>
      <nav aria-label="Evaluation sections">
        {NAV_ITEMS.map((item) => (
          <button key={item} type="button" onClick={() => scrollTo(item)}>
            {item}
          </button>
        ))}
      </nav>
      <div className="header-actions">
        <span className="backend-label">{backend}</span>
        <button className="primary-button" type="button" onClick={onRun} disabled={running}>
          <Play size={15} fill="currentColor" />
          {running ? "Evaluating…" : "Run evaluation"}
        </button>
      </div>
    </header>
  );
}

