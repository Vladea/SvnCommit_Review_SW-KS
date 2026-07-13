import { api } from './api';
import type { ScanResult, ScanStartResponse, ScanProgress, ScanMatchedLog } from './types';

export interface ScanStoreState {
  phase: 'idle' | 'querying' | 'preview_prompt' | 'scanning' | 'done';
  loading: boolean;
  error: string;
  result: ScanResult | null;
  startResp: ScanStartResponse | null;
  progress: ScanProgress | null;
  currentCommit: ScanMatchedLog | null;
}

type Listener = () => void;

let state: ScanStoreState = {
  phase: 'idle', loading: false, error: '',
  result: null, startResp: null, progress: null, currentCommit: null,
};

let listeners: Listener[] = [];
let timerId: ReturnType<typeof setInterval> | null = null;
let scanId: string | null = null;

const today = () => new Date().toISOString().split('T')[0];
const dateMinusDays = (d: number) => new Date(Date.now() - d * 86400000).toISOString().split('T')[0];

let _start = dateMinusDays(1);
let _end = today();
let _push = true;

function getDates() {
  return { start: _start, end: _end, push: _push };
}

function setDates(start: string, end: string, push: boolean) {
  _start = start; _end = end; _push = push;
}

function notify() {
  const s = { ...state };
  for (const fn of listeners) fn();
}

function stopPolling() {
  if (timerId) { clearInterval(timerId); timerId = null; }
}

function pollProgress() {
  if (!scanId) return;
  timerId = setInterval(async () => {
    try {
      const p = await api.get<ScanProgress>(`/api/scan/progress/${scanId}`, { timeout: 0 });
      state = { ...state, progress: p };
      if (p.current_project && p.current_revision) {
        const log = p.matched_logs?.find(
          (l: any) => l.project === p.current_project && l.revision === p.current_revision
        );
        if (log) state = { ...state, currentCommit: log };
      }
      if (p.status === 'done') {
        stopPolling();
        state = { ...state, phase: 'done', loading: false, result: p.result };
      } else if (p.status === 'error') {
        stopPolling();
        state = { ...state, phase: 'idle', loading: false, error: p.error || '未知错误' };
      }
      notify();
    } catch (e: any) {
      stopPolling();
      state = { ...state, phase: 'idle', loading: false, error: e.message };
      notify();
    }
  }, 1000);
}

async function doStartScan(start: string, end: string, push: boolean, preview: boolean) {
  stopPolling();
  state = { ...state, loading: true, error: '', result: null, progress: null, currentCommit: null };
  notify();

  try {
    const params = new URLSearchParams({
      start_date: start, end_date: end, push_teams: String(push),
    });
    if (preview) params.set('preview', 'true');

    const resp = await api.get<ScanStartResponse>(`/api/scan/start?${params.toString()}`, { timeout: 0 });
    state = { ...state, startResp: resp };

    if (resp.preview_triggered) {
      state = { ...state, phase: 'preview_prompt', loading: false };
      notify();
      return;
    }

    if (resp.scan_id) {
      scanId = resp.scan_id;
      state = { ...state, phase: 'scanning' };
      notify();
      pollProgress();
    }
  } catch (e: any) {
    state = { ...state, loading: false, error: e.message };
    notify();
  }
}

async function continueScan(start: string, end: string, push: boolean) {
  stopPolling();
  state = { ...state, loading: true, error: '', phase: 'scanning' };
  notify();

  try {
    const params = new URLSearchParams({
      start_date: start, end_date: end, push_teams: String(push),
      max_commits: '5',
    });
    const resp = await api.get<ScanStartResponse>(`/api/scan/start?${params.toString()}`, { timeout: 0 });
    if (resp.scan_id) {
      scanId = resp.scan_id;
      state = { ...state, phase: 'scanning' };
      notify();
      pollProgress();
    }
  } catch (e: any) {
    state = { ...state, loading: false, error: e.message };
    notify();
  }
}

function reset() {
  stopPolling();
  scanId = null;
  state = { phase: 'idle', loading: false, error: '', result: null, startResp: null, progress: null, currentCommit: null };
  notify();
}

export const scanStore = {
  subscribe(listener: Listener) {
    listeners = [...listeners, listener];
    return () => { listeners = listeners.filter(l => l !== listener); };
  },
  getSnapshot(): ScanStoreState {
    return state;
  },
  getDates,
  setDates,
  doStartScan,
  continueScan,
  reset,
};
