export interface Project {
  name: string;
  svn_url: string;
  enabled: boolean;
  owner_group: string;
  scan_window_days: number;
  teams_webhook_url: string;
}

export interface Report {
  id: number;
  date: string;
  start_date: string;
  end_date: string;
  repo_count: number;
  commit_count: number;
  file_count: number;
  author_count: number;
  p1: number;
  p2: number;
  p3: number;
  p4: number;
  teams: string;
}

export interface Issue {
  id: number;
  project: string;
  revision: string;
  author: string;
  level: string;
  type: string;
  engine: string;
  file: string;
  desc: string;
  suggestion: string;
  status: string;
}

export interface AuthorStat {
  author: string;
  commit_count: number;
  file_count: number;
  project_count: number;
  p1: number;
  p2: number;
  p3: number;
  p4: number;
  density: number;
}

export interface ScheduleEntry {
  hour: number;
  minute: number;
  enabled: boolean;
  notify_teams: boolean;
  notify_email: boolean;
}

export interface LLMProvider {
  id: string;
  name: string;
  type: string;
  api_base: string;
  api_key_ref: string;
  model: string;
  enabled: boolean;
  description: string;
}

export interface LLMSettings {
  default: string;
  fallback: string;
  concurrent: number;
  retry_count: number;
  retry_delay: number;
}

export interface NotificationCfg {
  teams: { enabled: boolean; webhook_url_ref: string };
  email: {
    enabled: boolean;
    smtp_host: string;
    smtp_port: number;
    smtp_user: string;
    smtp_password_ref: string;
    from_addr: string;
    to_addrs: string[];
  };
}

export interface ReviewRules {
  merge_conflict: boolean;
  todo_marker: boolean;
  debug_print: boolean;
  memory_safety: boolean;
}

export interface ScanResult {
  new_commit_count: number;
  matched_revision_count: number;
  skipped_by_date_count: number;
  report_id: number;
  errors: Array<{ project: string; revision: string; author: string; error: string }>;
  report: string;
}

export interface ScanStartResponse {
  scan_id: string;
  total_commits: number;
  matched_logs: ScanMatchedLog[];
  skipped_logs: ScanMatchedLog[];
  is_preview: boolean;
  preview_triggered: boolean;
}

export interface ScanMatchedLog {
  project: string;
  revision: string;
  author: string;
  commit_date_local: string;
  commit_time_local: string;
  error?: string;
}

export interface ScanProgress {
  status: string;
  total_commits: number;
  completed: number;
  current_project: string;
  current_revision: string;
  current_file: string;
  is_preview: boolean;
  matched_logs: ScanMatchedLog[];
  skipped_logs: ScanMatchedLog[];
  result: ScanResult | null;
  error: string | null;
}
