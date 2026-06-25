'use client';

import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { api } from '@/lib/api';
import { ScheduleEntry } from '@/lib/types';

const blank = (): ScheduleEntry => ({ hour: 18, minute: 0, enabled: true, notify_teams: true, notify_email: false });

export default function SchedulePage() {
  const [entries, setEntries] = useState<ScheduleEntry[]>([blank()]);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.get<ScheduleEntry[]>('/api/schedule').then(setEntries);
  }, []);

  const add = () => setEntries([...entries, blank()]);
  const remove = (i: number) => setEntries(entries.filter((_, idx) => idx !== i));
  const update = (i: number, k: keyof ScheduleEntry, v: any) => {
    const n = [...entries];
    (n[i] as any)[k] = v;
    setEntries(n);
  };

  const save = async () => {
    setSaving(true);
    try {
      await api.post('/api/schedule', { entries });
      api.post('/api/jobs/run-daily'); // trigger scan now
      alert('已保存并触发扫描');
    } finally { setSaving(false); }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-1">定时任务</h1>
      <p className="text-muted text-sm mb-5">配置多个定时扫描时段，每个时段独立控制通知渠道</p>
      {entries.map((e, i) => (
        <Card key={i} className="mb-3">
          <div className="flex items-end gap-4 flex-wrap">
            <Input label="时 (0-23)" type="number" min={0} max={23} className="w-24" value={e.hour} onChange={v => update(i, 'hour', +v.target.value)} />
            <Input label="分 (0-59)" type="number" min={0} max={59} className="w-24" value={e.minute} onChange={v => update(i, 'minute', +v.target.value)} />
            <label className="flex items-center gap-2 text-sm pb-3">
              <input type="checkbox" checked={e.enabled} onChange={v => update(i, 'enabled', (v.target as HTMLInputElement).checked)} />启用
            </label>
            <label className="flex items-center gap-2 text-sm pb-3">
              <input type="checkbox" checked={e.notify_teams} onChange={v => update(i, 'notify_teams', (v.target as HTMLInputElement).checked)} />Teams
            </label>
            <label className="flex items-center gap-2 text-sm pb-3">
              <input type="checkbox" checked={e.notify_email} onChange={v => update(i, 'notify_email', (v.target as HTMLInputElement).checked)} />Email
            </label>
            <Button variant="danger" size="sm" onClick={() => remove(i)}>删除</Button>
          </div>
        </Card>
      ))}
      <div className="flex gap-3 mt-4">
        <Button variant="ghost" onClick={add}>+ 添加时段</Button>
        <Button onClick={save} disabled={saving}>{saving ? '保存中...' : '保存并立即扫描'}</Button>
      </div>
    </div>
  );
}
