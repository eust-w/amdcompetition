# Dashboard visual specification

The implementation follows the generated primary-screen concept at:

`/Users/d-robotics/.codex/generated_images/019f64b1-e0bf-7a20-947f-9dc447a1a5bc/exec-7e485cf2-9c57-4c1e-ad91-bb50074fbbab.png`

## Design system

- Background: true near-black navy `#06111d`; no gradient surfaces or glass cards.
- Surfaces: `#091725` with single-pixel blue-gray borders.
- Primary evidence accent: cyan `#47d7ee`.
- Failure/recovery branch accent: coral `#ff7067`.
- Geometry: restrained 6–8 px radii and open grid panels.
- Typography: system sans for interface hierarchy; system monospace for hashes and runtime metadata.
- Motion: bar transitions and smooth section navigation only, disabled by `prefers-reduced-motion`.

## Information hierarchy

1. Evidence status and four aggregate metrics.
2. Per-seed paired comparison and immutable run provenance.
3. Failure taxonomy and one real episode's recovery timeline.
4. Downloadable artifacts and a data-derived trajectory preview.

## Intentional truth-preserving deviation

The generated concept contained a photoreal simulation thumbnail. Until the physical backend emits a real rendered frame, the implementation uses a data-derived SVG trajectory. This avoids presenting generated imagery as runtime evidence. A future physical run may add its actual frame/video as a hashed artifact.

