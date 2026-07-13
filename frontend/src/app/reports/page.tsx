'use client';

import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { api } from '@/lib/api';
import { Report } from '@/lib/types';

function viewReport(r: Report) {
  api.get<{ id: number; report: string }>(`/api/reports/${r.id}`).then(({ report }) => {
    const w = window.open('', '_blank', 'width=860,height=600');
    if (!w) return;
    w.document.title = `审查报告 #${r.id}  ${r.start_date} ~ ${r.end_date}`;
    w.document.body.style.margin = '0';
    w.document.body.style.padding = '20px';
    w.document.body.style.backgroundColor = '#fff';
    w.document.body.style.color = '#333';
    w.document.body.style.whiteSpace = 'pre-wrap';
    w.document.body.style.fontFamily = 'monospace';
    w.document.body.textContent = report;
  });
}

export default function ReportsPage() {
  const [reports, setReports] = useState<Report[]>([]);

  useEffect(() => {
    api.get<Report[]>('/api/reports').then(setReports);
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-1">审查报告</h1>
      <p className="text-muted text-sm mb-5">每次扫描生成一份报告，包含变更统计与问题汇总</p>

      {reports.length === 0 && (
        <div className="text-muted text-sm py-8 text-center">暂无报告，执行一次扫描后在此查看</div>
      )}

      <div className="space-y-3">
        {reports.map(r => (
          <Card key={r.id}>
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-3 mb-2">
                  <span className="text-xs font-mono text-muted bg-gray-100 px-2 py-0.5 rounded">#{r.id}</span>
                  <span className="text-sm font-medium">
                    {r.start_date === r.end_date ? r.start_date : `${r.start_date} ~ ${r.end_date}`}
                  </span>
                </div>

                <div className="flex gap-4 text-sm mb-2">
                  <span title="扫描仓库数"><span className="text-muted">📁</span> {r.repo_count} 仓库</span>
                  <span title="命中提交数"><span className="text-muted">📝</span> {r.commit_count} 提交</span>
                  <span title="变更文件数"><span className="text-muted">📄</span> {r.file_count} 文件</span>
                  <span title="涉及作者数"><span className="text-muted">👤</span> {r.author_count} 人</span>
                </div>

                <div className="flex items-center gap-2 flex-wrap">
                  {r.p1 > 0 && <Badge label={`P1: ${r.p1}`} />}
                  {r.p2 > 0 && <Badge label={`P2: ${r.p2}`} />}
                  {r.p3 > 0 && <Badge label={`P3: ${r.p3}`} />}
                  {r.p4 > 0 && <Badge label={`P4: ${r.p4}`} />}
                  {r.p1 + r.p2 + r.p3 + r.p4 === 0 && <span className="text-xs text-muted">✅ 无问题</span>}
                  {r.teams ? (() => {
                    try { const t = JSON.parse(r.teams); return <Badge label={t.teams?.ok ? '📢 Teams ✓' : '📢 Teams ✗'} />; }
                    catch { return null; }
                  })() : null}
                </div>
              </div>

              <Button size="sm" variant="ghost" onClick={() => viewReport(r)}>查看报告</Button>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
