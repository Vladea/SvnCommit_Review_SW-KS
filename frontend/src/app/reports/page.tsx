'use client';

import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { api } from '@/lib/api';
import { Report } from '@/lib/types';

export default function ReportsPage() {
  const [reports, setReports] = useState<Report[]>([]);

  useEffect(() => {
    api.get<Report[]>('/api/reports').then(setReports);
  }, []);

  const view = async (r: Report) => {
    const { report } = await api.get<{ id: number; report: string }>(`/api/reports/${r.id}`);
    const w = window.open('', '_blank', 'width=800,height=600');
    if (!w) return;
    w.document.title = `审查报告 ${r.date}`;
    w.document.body.style.whiteSpace = 'pre-wrap';
    w.document.body.style.fontFamily = 'monospace';
    w.document.body.style.padding = '20px';
    w.document.body.textContent = report;
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-1">审查报告</h1>
      <p className="text-muted text-sm mb-5">每日代码审查报告列表</p>
      <table>
        <thead><tr><th>日期</th><th>仓库</th><th>提交</th><th>文件</th><th>作者</th><th>P1</th><th>P2</th><th>P3</th><th>P4</th><th>Teams</th><th>操作</th></tr></thead>
        <tbody>
          {reports.map(r => (
            <tr key={r.id}>
              <td>{r.date}</td>
              <td>{r.repo_count}</td>
              <td>{r.commit_count}</td>
              <td>{r.file_count}</td>
              <td>{r.author_count}</td>
              <td><Badge label={`P1: ${r.p1}`} /></td>
              <td><Badge label={`P2: ${r.p2}`} /></td>
              <td><Badge label={`P3: ${r.p3}`} /></td>
              <td><Badge label={`P4: ${r.p4}`} /></td>
              <td>
                {r.teams ? (() => {
                  try { const t = JSON.parse(r.teams); return <Badge label={t.teams?.ok ? 'OK' : 'FAIL'} />; }
                  catch { return <Badge label="N/A" />; }
                })() : <Badge label="N/A" />}
              </td>
              <td><Button size="sm" variant="ghost" onClick={() => view(r)}>查看</Button></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
