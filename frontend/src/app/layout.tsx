'use client';

import { useState } from 'react';
import { Sidebar } from '@/components/sidebar';
import './globals.css';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <html lang="zh-CN">
      <body>
        <div className="flex min-h-screen">
          <Sidebar collapsed={collapsed} />
          <main className="flex-1 flex flex-col">
            <header className="flex items-center justify-between px-6 py-3 border-b border-[#d8e1ef] bg-white/60">
              <button onClick={() => setCollapsed(!collapsed)} className="text-xl bg-transparent border-0 cursor-pointer px-2">
                {collapsed ? '▶' : '◀'}
              </button>
              <span className="text-xs text-muted">SVN AI Review v2.0</span>
            </header>
            <div className="flex-1 p-6 overflow-auto">{children}</div>
          </main>
        </div>
      </body>
    </html>
  );
}
