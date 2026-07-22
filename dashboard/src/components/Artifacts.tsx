import { Download, ExternalLink, FileJson2 } from "lucide-react";
import { bytes, shortHash } from "../format";
import type { Manifest } from "../types";

export function Artifacts({ manifest }: { manifest: Manifest }) {
  const entries = Object.entries(manifest.files);
  return (
    <section className="panel artifacts-panel" id="artifacts">
      <div className="panel-heading">
        <div>
          <span className="section-label">Content-addressed run output</span>
          <h2>Artifacts</h2>
        </div>
      </div>
      <div className="artifact-list">
        {entries.map(([name, file]) => (
          <a href={`/api/artifacts/${name}`} key={name} download>
            <FileJson2 size={19} />
            <span><strong>{name}</strong><small>{bytes(file.bytes)}</small></span>
            <code>{shortHash(file.sha256)}</code>
            {name === "report.json" ? <ExternalLink size={16} /> : <Download size={16} />}
          </a>
        ))}
      </div>
    </section>
  );
}

