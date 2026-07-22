'use client';

import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { DatePicker } from '@/components/ui/datepicker';
import { scanStore } from '@/lib/scanStore';
import { api } from '@/lib/api';
import type { ScanStoreState } from '@/lib/scanStore';

const today = () => new Date().toISOString().split('T')[0];
const dateMinusDays = (d: number) => {
  const t = new Date(Date.now() - d * 86400000);
  return t.toISOString().split('T')[0];
};

const PRESETS = [
  { label: '本月', start: (() => { const t = new Date(); t.setDate(1); return t.toISOString().split('T')[0]; })(), end: today() },
  { label: '上周', start: dateMinusDays(14), end: dateMinusDays(7) },
  { label: '昨天', start: dateMinusDays(1), end: dateMinusDays(1) },
];

function useScanStore(): ScanStoreState {
  const [s, setS] = useState<ScanStoreState>(scanStore.getSnapshot());
  useEffect(() => scanStore.subscribe(() => setS(scanStore.getSnapshot())), []);
  return s;
}

export default function ScanPage() {
  const { start: initStart, end: initEnd, push: initPush } = scanStore.getDates();
  const [start, setStart] = useState(initStart);
  const [end, setEnd] = useState(initEnd);
  const [push, setPush] = useState(initPush);
  const [force, setForce] = useState(false);

  const s = useScanStore();

  const setStartPersist = (v: string) => { setStart(v); scanStore.setDates(v, end, push); };
  const setEndPersist = (v: string) => { setEnd(v); scanStore.setDates(start, v, push); };
  const setPushPersist = (v: boolean) => { setPush(v); scanStore.setDates(start, end, v); };

  const applyPreset = (p: typeof PRESETS[number]) => {
    setStart(p.start); setEnd(p.end); scanStore.setDates(p.start, p.end, push);
  };

  const pct = s.progress && s.progress.total_commits > 0
    ? Math.round((s.progress.completed / s.progress.total_commits) * 100)
    : 0;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-1">SVN 提交日期扫描</h1>
      <p className="text-muted text-sm mb-5">按 SVN 真实 commit 日期过滤，确保精确匹配</p>
      <Card className="mb-5">
        <div className="flex items-end gap-2 flex-wrap mb-3">
          <DatePicker label="开始日期" value={start} onChange={setStartPersist} min="2020-01-01" max={today()} />
          <span className="text-muted pb-2">—</span>
          <DatePicker label="结束日期" value={end} onChange={setEndPersist} min="2020-01-01" max={today()} />
          <label className="flex items-center gap-2 text-sm text-muted pb-2">
            <input type="checkbox" checked={push} onChange={e => setPushPersist((e.target as HTMLInputElement).checked)} />推送通知
          </label>
          <label className="flex items-center gap-2 text-sm text-orange-600 pb-2">
            <input type="checkbox" checked={force} onChange={e => setForce((e.target as HTMLInputElement).checked)} />强制重扫
          </label>
          <Button onClick={() => scanStore.doStartScan(start, end, push, true, force)} disabled={s.loading}>
            {s.loading && s.phase !== 'scanning' ? '查询中...' : '开始扫描'}
          </Button>
        </div>
        <div className="flex gap-2 flex-wrap">
          <span className="text-xs text-muted py-1">快速：</span>
          {PRESETS.map(p => (
            <button
              key={p.label}
              onClick={() => applyPreset(p)}
              disabled={s.loading}
              className="px-3 py-1 text-xs rounded-full border border-gray-300 bg-white hover:bg-blue-50 hover:border-primary text-gray-600 cursor-pointer disabled:opacity-50"
            >
              {p.label}
            </button>
          ))}
        </div>
      </Card>

      {s.error && <div className="bg-red-50 text-danger px-4 py-3 rounded-btn mb-4">{s.error}</div>}

      {/* Preview prompt */}
      {s.phase === 'preview_prompt' && s.startResp && (
        <Card>
          <div className="text-center py-4">
            <p className="text-lg mb-2">
              找到 <b className="text-primary">{s.startResp.total_commits}</b> 个 Commit
            </p>
            <p className="text-muted text-sm mb-4">建议先预览前 5 个 Commit 快速验证配置</p>
            <div className="flex gap-3 justify-center">
              <Button onClick={() => scanStore.continueScan(start, end, push, force)}>预览前 5 个</Button>
              <Button variant="ghost" onClick={() => scanStore.doStartScan(start, end, push, false, force)}>
                直接扫描全部 ({s.startResp.total_commits})
              </Button>
            </div>
          </div>
          {s.startResp.matched_logs.length > 0 && (
            <div className="mt-4 max-h-60 overflow-y-auto">
              <table>
                <thead><tr><th>项目</th><th>Revision</th><th>提交人</th><th>日期</th><th>时间</th></tr></thead>
                <tbody>
                  {s.startResp.matched_logs.map((log: any, i: number) => (
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
      {s.phase === 'scanning' && s.progress && (
        <Card>
          <div className="mb-4">
            <div className="flex justify-between text-sm mb-1">
              <span className="text-muted">{s.progress.status === 'done' ? '扫描完成' : '正在扫描...'}</span>
              <span className="font-medium">{s.progress.completed} / {s.progress.total_commits}</span>
            </div>
            <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-300 ${s.progress.status === 'done' ? 'bg-green-500' : 'bg-primary'}`}
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>
          {s.progress.current_project && (
            <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-sm bg-gray-50 rounded-btn p-4">
              <div><span className="text-muted">项目：</span><b>{s.progress.current_project}</b></div>
              <div>
                <span className="text-muted">Revision：</span>
                <b className="font-mono">{s.progress.current_revision}</b>
                {s.currentCommit && <span className="ml-2 text-xs text-muted">{s.currentCommit.author} · {s.currentCommit.commit_date_local}</span>}
              </div>
            </div>
          )}
        </Card>
      )}

      {/* Result */}
      {s.result && (
        <Card>
          <div className="grid grid-cols-4 gap-4 mb-4">
            <div><b className="text-2xl">{s.result.new_commit_count}</b><span className="ml-2 text-muted text-sm">新提交</span></div>
            <div><b className="text-2xl">{s.result.matched_revision_count}</b><span className="ml-2 text-muted text-sm">命中 Revision</span></div>
            <div><b className="text-2xl">{s.result.skipped_by_date_count}</b><span className="ml-2 text-muted text-sm">被过滤</span></div>
            <div><b className="text-2xl">{s.result.errors.length}</b><span className="ml-2 text-muted text-sm">异常</span></div>
          </div>
          <div className="flex gap-3">
            <Button onClick={() => {
              if (!s.result) return;
              const rid = s.result.report_id;
              const w = window.open('', '_blank', 'width=860,height=600');
              if (!w) return;
              w.document.title = `审查报告 #${rid}`;
              w.document.body.textContent = '加载中...';
              api.get<{ id: number; report: string }>(`/api/reports/${rid}`).then(({ report }) => {
                w.document.body.style.margin = '0';
                w.document.body.style.padding = '20px';
                w.document.body.style.backgroundColor = '#fff';
                w.document.body.style.color = '#333';
                w.document.body.style.whiteSpace = 'pre-wrap';
                w.document.body.style.fontFamily = 'monospace';
                w.document.body.textContent = report;
              });
            }}>查看完整报告</Button>
          </div>
          {s.result.errors.length > 0 && (
            <div className="mt-4">
              <h3 className="font-semibold text-danger mb-2">异常 ({s.result.errors.length})</h3>
              {s.result.errors.map((e, i) => (
                <div key={i} className="text-xs text-muted mb-1">[{e.project}] r{e.revision} — {e.error}</div>
              ))}
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
