'use client';

import { usePathname } from 'next/navigation';

const nav = [
  { id: 'dashboard', label: '仪表盘', icon: '📊' },
  { id: 'projects', label: '项目白名单', icon: '📁' },
  { id: 'scan', label: 'SVN 日期扫描', icon: '📅' },
  { id: 'schedule', label: '定时任务', icon: '⏰' },
  { id: 'reports', label: '审查报告', icon: '📋' },
  { id: 'issues', label: '问题列表', icon: '🚨' },
  { id: 'authors', label: '提交人统计', icon: '👥' },
  { id: 'settings', label: '全局设置', icon: '⚙️' },
];

export function Sidebar({ collapsed }: { collapsed: boolean }) {
  const path = usePathname();
  const current = path.replace(/\//g, '') || 'dashboard';

  return (
    <aside className={`bg-sidebar border-r border-[#d8e1ef] shadow-lg flex flex-col transition-all ${collapsed ? 'w-16' : 'w-60'}`}>
      <div className="flex items-center gap-3 p-5 border-b border-[#d8e1ef]">
        <div className="min-w-[42px] h-[42px] rounded-xl bg-gradient-to-br from-primary to-primary-light text-white grid place-items-center font-extrabold text-lg">AI</div>
        {!collapsed && <div className="leading-tight"><b className="text-sm">SVN AI Review</b><span className="block text-xs text-muted">v2.0</span></div>}
      </div>
      <nav className="flex-1 p-2 space-y-0.5">
        {nav.map(({ id, label, icon }) => {
          const active = current === id;
          return (
            <a
              key={id}
              href={`/${id === 'dashboard' ? '' : id}`}
              className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium no-underline transition-colors
                ${active ? 'bg-blue-50 text-primary' : 'text-gray-600 hover:bg-blue-50/50'}`}
            >
              <span className="text-lg">{icon}</span>
              {!collapsed && label}
            </a>
          );
        })}
      </nav>
    </aside>
  );
}
