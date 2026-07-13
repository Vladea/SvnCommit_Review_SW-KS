'use client';

import { useState, useRef, useCallback } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { api } from '@/lib/api';
import { ScanResult, ScanStartResponse, ScanProgress, ScanMatchedLog } from '@/lib/types';

export default function ScanPage() {
  const today = new Date().toISOString().split('T')[0];
  const yesterday = new Date(Date.now() - 86400000).toISOString().split('T')[0];
  const [start, setStart] = useState(yesterday);
  const [end, setEnd] = useState(today);
  const [push, setPush] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<ScanResult | null>(null);
  const [phase, setPhase] = useState<'idle' | 'querying' | 'preview_prompt' | 'scanning' | 'done'>('idle');
  const [startResp, setStartResp] = useState<ScanStartResponse | null>(null);
  const [progress, setProgress] = useState<ScanProgress | null>(null);
  const [currentCommit, setCurrentCommit] = useState<ScanMatchedLog | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPolling = useCallback(() => {
    if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; }
  }, []);

  const pollProgress = useCallback((scanId: string) => {
    stopPolling();
    timerRef.current = setInterval(async () => {
      try {
        const p = await api.get<ScanProgress>(`/api/scan/progress/${scanId}`, { timeout: 0 });
        setProgress(p);
        if (p.current_project && p.current_revision) {
          const log = p.matched_logs?.find(
            (l: ScanMatchedLog) => l.project === p.current_project && l.revision === p.current_revision
          );
          if (log) setCurrentCommit(log);
        }
        if (p.status === 'done') {
          stopPolling();
          setResult(p.result);
          setPhase('done');
          setLoading(false);
        } else if (p.status === 'error') {
          stopPolling();
          setError(p.error || '未知错误');
          setPhase('idle');
          setLoading(false);
        }
      } catch (e: any) {
        stopPolling();
        setError(e.message);
        setPhase('idle');
        setLoading(false);
      }
    }, 1000);
  }, [stopPolling]);

  const doStartScan = async (preview: boolean, maxCommits?: number) => {
    setLoading(true); setError(''); setResult(null); setProgress(null); setCurrentCommit(null);
    stopPolling();

    try {
      const params = new URLSearchParams({
        start_date: start, end_date: end, push_teams: String(push),
      });
      if (preview) params.set('preview', 'true');
      if (maxCommits) params.set('max_commits', String(maxCommits));

      const resp = await api.get<ScanStartResponse>(
        `/api/scan/start?${params.toString()}`,
        { timeout: 0 }
      );
      setStartResp(resp);

      if (resp.preview_triggered) {
        setPhase('preview_prompt');
        setLoading(false);
        return;
      }

      if (resp.scan_id) {
        setPhase('scanning');
        pollProgress(resp.scan_id);
      }
    } catch (e: any) {
      setError(e.message);
      setLoading(false);
    }
  };

  const continueScan = async () => {
    setLoading(true); setError(''); setPhase('scanning');
    try {
      const params = new URLSearchParams({
        start_date: start, end_date: end, push_teams: String(push),
        max_commits: '5',
      });
      const resp = await api.get<ScanStartResponse>(
        `/api/scan/start?${params.toString()}`,
        { timeout: 0 }
      );
      if (resp.scan_id) {
        pollProgress(resp.scan_id);
      }
    } catch (e: any) {
      setError(e.message);
      setLoading(false);
    }
  };

  const pct = progress && progress.total_commits > 0
    ? Math.round((progress.completed / progress.total_commits) * 100)
    : 0;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-1">SVN 提交日期扫描</h1>
      <p className="text-muted text-sm mb-5">按 SVN 真实 commit 日期过滤，确保精确匹配</p>
      <Card className="mb-5">
        <div className="flex items-end gap-4 flex-wrap">
          <Input label="开始日期" type="date" value={start} onChange={e => setStart(e.target.value)} />
          <Input label="结束日期" type="date" value={end} onChange={e => setEnd(e.target.value)} />
          <label className="flex items-center gap-2 text-sm text-muted pb-3">
            <input type="checkbox" checked={push} onChange={e => setPush((e.target as HTMLInputElement).checked)} />推送通知
          </label>
          <Button onClick={() => doStartScan(true)} disabled={loading}>
            {loading && phase !== 'scanning' ? '查询中...' : '开始扫描'}
          </Button>
        </div>
      </Card>

      {error && <div className="bg-red-50 text-danger px-4 py-3 rounded-btn mb-4">{error}</div>}

      {/* Preview prompt */}
      {phase === 'preview_prompt' && startResp && (
        <Card>
          <div className="text-center py-4">
            <p className="text-lg mb-2">
              找到 <b className="text-primary">{startResp.total_commits}</b> 个 Commit
            </p>
            <p className="text-muted text-sm mb-4">建议先预览前 5 个 Commit 快速验证配置</p>
            <div className="flex gap-3 justify-center">
              <Button onClick={continueScan}>预览前 5 个</Button>
              <Button variant="ghost" onClick={() => doStartScan(false, startResp.total_commits)}>
                直接扫描全部 ({startResp.total_commits})
              </Button>
            </div>
          </div>
          {startResp.matched_logs.length > 0 && (
            <div className="mt-4 max-h-60 overflow-y-auto">
              <table>
                <thead><tr><th>项目</th><th>Revision</th><th>提交人</th><th>日期</th><th>时间</th></tr></thead>
                <tbody>
                  {startResp.matched_logs.map((log, i) => (
                    <tr key={i} className={log.error ? 'text-danger' : ''}>
                      <td>{log.project}</td>
                      <td className="font-mono">{log.revision}</td>
                      <td>{log.author}</td>
                      <td>{log.commit_date_local}</td>
                      <td className="text-xs text-muted">{log.commit_time_local}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}

      {/* Scanning progress */}
      {phase === 'scanning' && progress && (
        <Card>
          <div className="mb-4">
            <div className="flex justify-between text-sm mb-1">
              <span className="text-muted">{progress.status === 'done' ? '扫描完成' : '正在扫描...'}</span>
              <span className="font-medium">{progress.completed} / {progress.total_commits}</span>
            </div>
            <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-300 ${progress.status === 'done' ? 'bg-green-500' : 'bg-primary'}`}
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>
          {progress.current_project && (
            <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-sm bg-gray-50 rounded-btn p-4">
              <div><span className="text-muted">项目：</span><b>{progress.current_project}</b></div>
              <div>
                <span className="text-muted">Revision：</span>
                <b className="font-mono">{progress.current_revision}</b>
                {currentCommit && <span className="ml-2 text-xs text-muted">{currentCommit.author} · {currentCommit.commit_date_local}</span>}
              </div>
              <div className="col-span-2"><span className="text-muted">文件：</span><span className="text-xs font-mono break-all">{progress.current_file || '—'}</span></div>
            </div>
          )}
        </Card>
      )}

      {/* Result */}
      {result && (
        <Card>
          <div className="grid grid-cols-4 gap-4 mb-4">
            <div><b className="text-2xl">{result.new_commit_count}</b><span className="ml-2 text-muted text-sm">新提交</span></div>
            <div><b className="text-2xl">{result.matched_revision_count}</b><span className="ml-2 text-muted text-sm">命中 Revision</span></div>
            <div><b className="text-2xl">{result.skipped_by_date_count}</b><span className="ml-2 text-muted text-sm">被过滤</span></div>
            <div><b className="text-2xl">{result.errors.length}</b><span className="ml-2 text-muted text-sm">异常</span></div>
          </div>
          <div className="flex gap-3">
            <Button onClick={() => window.open(`/reports?id=${result.report_id}`, '_blank')}>查看报告 #{result.report_id}</Button>
          </div>
          {result.errors.length > 0 && (
            <div className="mt-4">
              <h3 className="font-semibold text-danger mb-2">异常 ({result.errors.length})</h3>
              {result.errors.map((e, i) => (
                <div key={i} className="text-xs text-muted mb-1">[{e.project}] r{e.revision} — {e.error}</div>
              ))}
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
