'use client';

import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { api } from '@/lib/api';
import { Project } from '@/lib/types';

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [form, setForm] = useState({ name: '', svn_url: '', owner_group: '', teams_webhook_url: '' });

  const load = () => api.get<Project[]>('/api/projects').then(setProjects);

  useEffect(() => { load(); }, []);

  const save = async () => {
    await api.post('/api/projects', { ...form, enabled: true, scan_window_days: 1 });
    setForm({ name: '', svn_url: '', owner_group: '', teams_webhook_url: '' });
    load();
  };

  const toggle = (name: string, en: boolean) => {
    api.post(`/api/projects/${encodeURIComponent(name)}/${en ? 'enable' : 'disable'}`).then(load);
  };

  const del = (name: string) => {
    if (confirm(`确认删除 ${name} ?`)) api.del(`/api/projects/${encodeURIComponent(name)}`).then(load);
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-1">项目白名单</h1>
      <p className="text-muted text-sm mb-5">完整 SVN URL，分支直接体现在 URL 中</p>
      <Card className="mb-5">
        <div className="grid grid-cols-4 gap-3 mb-3">
          <Input placeholder="项目名" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} />
          <Input placeholder="SVN URL" value={form.svn_url} onChange={e => setForm({ ...form, svn_url: e.target.value })} />
          <Input placeholder="负责人/团队" value={form.owner_group} onChange={e => setForm({ ...form, owner_group: e.target.value })} />
          <Input placeholder="Teams Webhook（可选）" value={form.teams_webhook_url} onChange={e => setForm({ ...form, teams_webhook_url: e.target.value })} />
        </div>
        <Button onClick={save}>添加项目</Button>
      </Card>
      <table>
        <thead><tr><th>启用</th><th>项目</th><th>SVN URL</th><th>团队</th><th>操作</th></tr></thead>
        <tbody>
          {projects.map(p => (
            <tr key={p.name}>
              <td>{p.enabled ? '✅' : '❌'}</td>
              <td className="font-medium">{p.name}</td>
              <td className="text-xs text-muted max-w-xs truncate">{p.svn_url}</td>
              <td>{p.owner_group || '-'}</td>
              <td className="flex gap-2">
                <Button size="sm" variant="ghost" onClick={() => toggle(p.name, !p.enabled)}>{p.enabled ? '禁用' : '启用'}</Button>
                <Button size="sm" variant="danger" onClick={() => del(p.name)}>删除</Button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
