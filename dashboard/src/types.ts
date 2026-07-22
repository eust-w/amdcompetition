export type FailureRow = {
  failure_type: string;
  injected: number;
  baseline_failed: number;
  detected: number;
  recovered: number;
  recovery_rate: number;
  mean_recovery_latency_ms: number;
};

export type SeedRow = {
  seed: number;
  episodes: number;
  baseline_success_rate: number;
  recovery_success_rate: number;
};

export type AttemptState = {
  state: string;
  t_ms: number;
  status: "ok" | "failed";
  failure?: string;
};

export type Attempt = {
  attempt_index: number;
  success: boolean;
  failure_kind: string;
  confidence: number;
  aim_error_m: number;
  pose_error_rad: number;
  hold_margin: number;
  object_height_m: number;
  simulated_latency_ms: number;
  states: AttemptState[];
};

export type ExampleRecovery = {
  episode_id: string;
  scenario: {
    injected_failure: string;
    object_x_m: number;
    object_y_m: number;
  };
  baseline: { success: boolean; attempts: Attempt[] };
  recovery: { success: boolean; retries: number; attempts: Attempt[] };
};

export type Report = {
  schema_version: string;
  run_id: string;
  benchmark: string;
  config_digest: string;
  result_digest: string;
  git_commit: string;
  runtime: {
    python: string;
    platform: string;
    wall_time_seconds: number;
  };
  backend_evidence: {
    backend: string;
    engine: string;
    physics: boolean;
    accelerator: string;
    rocm_verified: boolean;
    devices?: string[];
    hip_version?: string;
    claim_boundary?: string;
  };
  metrics: {
    episodes: number;
    baseline_successes: number;
    baseline_success_rate: number;
    recovery_successes: number;
    recovery_success_rate: number;
    baseline_failures: number;
    recovered_failures: number;
    failure_recovery_rate: number;
    failure_detection_rate: number;
    mean_retries: number;
    absolute_success_lift: number;
    failure_taxonomy: FailureRow[];
    per_seed: SeedRow[];
  };
  example_recovery: ExampleRecovery | null;
};

export type Manifest = {
  run_id: string;
  files: Record<string, { sha256: string; bytes: number }>;
};

export type ReproducibilityCertificate = {
  passed: boolean;
  tolerance: number;
  left_result_digest: string;
  right_result_digest: string;
  metric_deltas: Record<string, number>;
};

export type LatestResponse = {
  report: Report;
  manifest: Manifest;
  reproducibility?: ReproducibilityCertificate;
};

