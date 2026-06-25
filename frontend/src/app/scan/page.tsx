'use client';

import { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { api } from '@/lib/api';
import { ScanResult } from '@/lib/types';

export default function ScanPage() {
  const today = new Date().toISOString().split('T')[0];
  const yesterday = new Date(Date.now() - 86400000).toISOString().split('T')[0];
  const [start, setStart] = useState(yesterday);
  const [end, setEnd] = useState(today);
  const [push, setPush] = useState(true);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ScanResult | null>(null);
  const [error, setError] = useState('');

  const scan = async () => {
    setLoading(true); setError(''); setResult(null);
    try {
      const r = await api.post<ScanResult>('/api/scan/range', { start_date: start, end_date: end, project_names: null, push_teams: push });
      setResult(r);
    } catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  };

  const openReport = (id: number) => window.open(`/reports?id=${id}`, '_blank');

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
          <Button onClick={scan} disabled={loading}>{loading ? '扫描中...' : '开始扫描'}</Button>
        </div>
      </Card>
      {error && <div className="bg-red-50 text-danger px-4 py-3 rounded-btn mb-4">{error}</div>}
      {result && (
        <Card>
          <div className="grid grid-cols-4 gap-4 mb-4">
            <div><b className="text-2xl">{result.new_commit_count}</b><span className="ml-2 text-muted text-sm">新提交</span></div>
            <div><b className="text-2xl">{result.matched_revision_count}</b><span className="ml-2 text-muted text-sm">命中 Revision</span></div>
            <div><b className="text-2xl">{result.skipped_by_date_count}</b><span className="ml-2 text-muted text-sm">被过滤</span></div>
            <div><b className="text-2xl">{result.errors.length}</b><span className="ml-2 text-muted text-sm">异常</span></div>
          </div>
          <Button onClick={() => openReport(result.report_id)}>查看报告 #{result.report_id}</Button>
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
