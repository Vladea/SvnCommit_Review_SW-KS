'use client';

import { useEffect, useState } from 'react';
import { StatsCard } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { api } from '@/lib/api';
import { Report } from '@/lib/types';

export default function DashboardPage() {
  const [commit, setCommit] = useState(0);
  const [issue, setIssue] = useState(0);
  const [rpt, setRpt] = useState(0);
  const [latest, setLatest] = useState('');

  useEffect(() => {
    api.get<{ commit_count: number; issue_count: number; report_count: number; latest_report: string }>('/api/dashboard/summary').then(d => {
      setCommit(d.commit_count);
      setIssue(d.issue_count);
      setRpt(d.report_count);
      setLatest(d.latest_report || '暂无报告');
    });
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-1">仪表盘</h1>
      <p className="text-muted text-sm mb-5">v2.0 · 日期级扫描 · AI 可插拔审查</p>
      <div className="grid grid-cols-3 gap-4 mb-5">
        <StatsCard value={commit} label="提交记录" />
        <StatsCard value={issue} label="Review 问题" />
        <StatsCard value={rpt} label="历史报告" />
      </div>
      <div className="bg-card border border-[#d8e1ef] rounded-card p-5 shadow-lg">
        <h2 className="text-base font-semibold mb-3 text-gray-700">最新日报</h2>
        <pre>{latest}</pre>
      </div>
    </div>
  );
}
