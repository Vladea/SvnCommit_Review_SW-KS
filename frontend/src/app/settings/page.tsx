'use client';

import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { api } from '@/lib/api';
import { LLMProvider, LLMSettings, NotificationCfg, ReviewRules } from '@/lib/types';

const blankProvider = (): LLMProvider => ({
  id: '', name: '', type: 'openai_compatible', api_base: '', api_key_ref: '', model: '', enabled: true, description: ''
});

export default function SettingsPage() {
  const [tab, setTab] = useState<'llm' | 'notify' | 'rules'>('llm');
  const [providers, setProviders] = useState<LLMProvider[]>([]);
  const [llmSettings, setLlmSettings] = useState<LLMSettings>({ default: '', fallback: '', concurrent: 3, retry_count: 2, retry_delay: 5 });
  const [notifyCfg, setNotifyCfg] = useState<NotificationCfg | null>(null);
  const [rules, setRules] = useState<ReviewRules>({ merge_conflict: true, todo_marker: true, debug_print: true, memory_safety: true });
  const [editProv, setEditProv] = useState<LLMProvider>(blankProvider());
  const [showForm, setShowForm] = useState(false);
  const [testMsg, setTestMsg] = useState('');

  useEffect(() => {
    api.get<LLMProvider[]>('/api/settings/llm/providers').then(setProviders);
    api.get<LLMSettings>('/api/settings/llm/settings').then(setLlmSettings);
    api.get<NotificationCfg>('/api/settings/notifications').then(setNotifyCfg);
    api.get<ReviewRules>('/api/settings/rules').then(setRules);
  }, []);

  const reload = () => {
    api.get<LLMProvider[]>('/api/settings/llm/providers').then(setProviders);
  };

  const saveProvider = async () => {
    const exists = providers.find(p => p.id === editProv.id);
    if (exists) {
      await api.put(`/api/settings/llm/providers/${editProv.id}`, editProv);
    } else {
      await api.post('/api/settings/llm/providers', editProv);
    }
    setShowForm(false); reload();
  };

  const delProvider = async (id: string) => {
    if (confirm(`删除 ${id} ?`)) { await api.del(`/api/settings/llm/providers/${id}`); reload(); }
  };

  const testProvider = async (id: string) => {
    const r = await api.post<{ ok: boolean; elapsed_ms: number; detail: string }>(`/api/settings/llm/providers/${id}/test`);
    setTestMsg(r.ok ? `连接成功 (${r.elapsed_ms}ms): ${r.detail}` : `连接失败 (${r.elapsed_ms}ms): ${r.detail}`);
  };

  const toggleProv = async (id: string, en: boolean) => {
    await api.post(`/api/settings/llm/providers/${id}/${en ? 'enable' : 'disable'}`); reload();
  };

  const saveLlm = () => api.put('/api/settings/llm/settings', llmSettings).then(() => alert('LLM 全局设置已保存'));
  const saveNotify = () => notifyCfg && api.put('/api/settings/notifications', notifyCfg).then(() => alert('通知设置已保存'));
  const saveRules = () => api.put('/api/settings/rules', rules).then(() => alert('规则开关已保存'));

  const tabs = [
    { id: 'llm' as const, label: 'LLM 提供商' },
    { id: 'notify' as const, label: '通知配置' },
    { id: 'rules' as const, label: '审查规则' },
  ];

  return (
    <div>
      <h1 className="text-2xl font-bold mb-1">全局设置</h1>
      <p className="text-muted text-sm mb-5">LLM 接口 · 通知渠道 · 审查规则</p>

      <div className="flex gap-2 mb-5">
        {tabs.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`px-5 py-2 rounded-btn text-sm font-medium border-0 cursor-pointer transition-colors ${tab === t.id ? 'bg-primary text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}>
            {t.label}
          </button>
        ))}
      </div>

      {/* LLM Tab */}
      {tab === 'llm' && (
        <div className="space-y-4">
          <Card title="LLM 全局设置">
            <div className="grid grid-cols-3 gap-3 mb-3">
              <Input label="默认提供商 ID" value={llmSettings.default} onChange={e => setLlmSettings({ ...llmSettings, default: e.target.value })} />
              <Input label="备选提供商 ID" value={llmSettings.fallback} onChange={e => setLlmSettings({ ...llmSettings, fallback: e.target.value })} />
              <Input label="并发数" type="number" value={llmSettings.concurrent} onChange={e => setLlmSettings({ ...llmSettings, concurrent: +e.target.value })} />
              <Input label="重试次数" type="number" value={llmSettings.retry_count} onChange={e => setLlmSettings({ ...llmSettings, retry_count: +e.target.value })} />
              <Input label="重试间隔(秒)" type="number" value={llmSettings.retry_delay} onChange={e => setLlmSettings({ ...llmSettings, retry_delay: +e.target.value })} />
            </div>
            <Button onClick={saveLlm}>保存全局设置</Button>
          </Card>

          <Card title={`提供商列表 (${providers.length})`}>
            {testMsg && <div className="bg-blue-50 text-primary px-4 py-3 rounded-btn mb-3 text-sm">{testMsg}</div>}
            <table className="mb-3">
              <thead><tr><th>启用</th><th>名称</th><th>API Base</th><th>Model</th><th>Key 变量</th><th>操作</th></tr></thead>
              <tbody>
                {providers.map(p => (
                  <tr key={p.id}>
                    <td>{p.enabled ? '✅' : '❌'}</td>
                    <td className="font-medium">{p.name}</td>
                    <td className="text-xs text-muted max-w-[200px] truncate">{p.api_base}</td>
                    <td className="text-xs font-mono">{p.model}</td>
                    <td className="text-xs text-muted">{p.api_key_ref || '无'}</td>
                    <td className="flex gap-1 flex-wrap">
                      <Button size="sm" variant="ghost" onClick={() => toggleProv(p.id, !p.enabled)}>{p.enabled ? '禁用' : '启用'}</Button>
                      <Button size="sm" variant="ghost" onClick={() => { setEditProv(p); setShowForm(true); }}>编辑</Button>
                      <Button size="sm" variant="ghost" onClick={() => testProvider(p.id)}>测试</Button>
                      <Button size="sm" variant="danger" onClick={() => delProvider(p.id)}>删除</Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <Button onClick={() => { setEditProv(blankProvider()); setShowForm(true); }}>+ 添加 AI 接口</Button>
          </Card>

          {showForm && (
            <Card title={editProv.id ? `编辑: ${editProv.id}` : '添加 AI 接口'}>
              <div className="grid grid-cols-2 gap-3 mb-3">
                <Input label="ID (唯一标识)" value={editProv.id} onChange={e => setEditProv({ ...editProv, id: e.target.value })} />
                <Input label="名称" value={editProv.name} onChange={e => setEditProv({ ...editProv, name: e.target.value })} />
                <Input label="API Base URL" value={editProv.api_base} onChange={e => setEditProv({ ...editProv, api_base: e.target.value })} />
                <Input label="模型名" value={editProv.model} onChange={e => setEditProv({ ...editProv, model: e.target.value })} />
                <Input label=".env 变量名 (存储 API Key)" value={editProv.api_key_ref} onChange={e => setEditProv({ ...editProv, api_key_ref: e.target.value })} />
                <Input label="描述" value={editProv.description} onChange={e => setEditProv({ ...editProv, description: e.target.value })} />
              </div>
              <div className="flex gap-3">
                <Button onClick={saveProvider}>保存</Button>
                <Button variant="ghost" onClick={() => setShowForm(false)}>取消</Button>
              </div>
            </Card>
          )}
        </div>
      )}

      {/* Notify Tab */}
      {tab === 'notify' && notifyCfg && (
        <div className="space-y-4">
          <Card title="Teams 通知">
            <label className="flex items-center gap-2 mb-3">
              <input type="checkbox" checked={notifyCfg.teams.enabled} onChange={e => setNotifyCfg({ ...notifyCfg, teams: { ...notifyCfg.teams, enabled: (e.target as HTMLInputElement).checked } })} />启用
            </label>
            <Input label="Webhook URL .env 变量名" value={notifyCfg.teams.webhook_url_ref} onChange={e => setNotifyCfg({ ...notifyCfg, teams: { ...notifyCfg.teams, webhook_url_ref: e.target.value } })} />
            <div className="mt-3"><Button size="sm" variant="ghost" onClick={() => api.post<{ ok: boolean; msg: string }>('/api/settings/notifications/teams/test').then(r => setTestMsg(JSON.stringify(r)))}>测试 Teams</Button></div>
          </Card>
          <Card title="Email 通知">
            <label className="flex items-center gap-2 mb-3">
              <input type="checkbox" checked={notifyCfg.email.enabled} onChange={e => setNotifyCfg({ ...notifyCfg, email: { ...notifyCfg.email, enabled: (e.target as HTMLInputElement).checked } })} />启用
            </label>
            <div className="grid grid-cols-2 gap-3 mb-3">
              <Input label="SMTP 主机" value={notifyCfg.email.smtp_host} onChange={e => setNotifyCfg({ ...notifyCfg, email: { ...notifyCfg.email, smtp_host: e.target.value } })} />
              <Input label="端口" type="number" value={notifyCfg.email.smtp_port} onChange={e => setNotifyCfg({ ...notifyCfg, email: { ...notifyCfg.email, smtp_port: +e.target.value } })} />
              <Input label="用户名" value={notifyCfg.email.smtp_user} onChange={e => setNotifyCfg({ ...notifyCfg, email: { ...notifyCfg.email, smtp_user: e.target.value } })} />
              <Input label="密码 .env 变量名" value={notifyCfg.email.smtp_password_ref} onChange={e => setNotifyCfg({ ...notifyCfg, email: { ...notifyCfg.email, smtp_password_ref: e.target.value } })} />
              <Input label="发件人地址" value={notifyCfg.email.from_addr} onChange={e => setNotifyCfg({ ...notifyCfg, email: { ...notifyCfg.email, from_addr: e.target.value } })} />
              <Input label="收件人 (逗号分隔)" value={notifyCfg.email.to_addrs.join(', ')} onChange={e => setNotifyCfg({ ...notifyCfg, email: { ...notifyCfg.email, to_addrs: e.target.value.split(',').map(s => s.trim()).filter(Boolean) } })} />
            </div>
            <div className="mt-3"><Button size="sm" variant="ghost" onClick={() => api.post<{ ok: boolean; msg: string }>('/api/settings/notifications/email/test').then(r => setTestMsg(JSON.stringify(r)))}>测试 Email</Button></div>
          </Card>
          <Button onClick={saveNotify}>保存通知设置</Button>
          {testMsg && <div className="mt-3 bg-blue-50 text-primary px-4 py-3 rounded-btn text-sm">{testMsg}</div>}
        </div>
      )}

      {/* Rules Tab */}
      {tab === 'rules' && (
        <Card title="审查规则开关">
          <p className="text-muted text-sm mb-4">启用或禁用各项自动审查规则。关闭后该规则不再检查。</p>
          <div className="space-y-3">
            {[
              { key: 'merge_conflict', label: '合并冲突标记', desc: '检查 <<<<<<< / >>>>>>> / =======', level: 'P1' },
              { key: 'todo_marker', label: 'TODO/FIXME 标记', desc: '检查待办和修复标记', level: 'P4' },
              { key: 'debug_print', label: '调试输出语句', desc: '检查 printf / System.out.println', level: 'P3' },
              { key: 'memory_safety', label: 'memcpy 边界检查', desc: '检查 memcpy 是否有长度保护', level: 'P3' },
            ].map(r => (
              <label key={r.key} className="flex items-center gap-3 p-3 bg-gray-50 rounded-btn cursor-pointer hover:bg-gray-100">
                <input type="checkbox" checked={(rules as any)[r.key]} onChange={e => setRules({ ...rules, [r.key]: (e.target as HTMLInputElement).checked })} />
                <div>
                  <div className="font-medium text-sm">{r.label} <Badge label={r.level} /></div>
                  <div className="text-xs text-muted">{r.desc}</div>
                </div>
              </label>
            ))}
          </div>
          <div className="mt-4"><Button onClick={saveRules}>保存规则</Button></div>
        </Card>
      )}
    </div>
  );
}
