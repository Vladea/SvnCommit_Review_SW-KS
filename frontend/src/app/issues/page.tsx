'use client';

import { useEffect, useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { api } from '@/lib/api';
import { Issue } from '@/lib/types';

export default function IssuesPage() {
  const [issues, setIssues] = useState<Issue[]>([]);

  useEffect(() => {
    api.get<Issue[]>('/api/issues').then(setIssues);
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-5">问题列表</h1>
      <table>
        <thead><tr><th>级别</th><th>引擎</th><th>项目</th><th>Revision</th><th>作者</th><th>类型</th><th>文件</th><th>描述</th><th>建议</th></tr></thead>
        <tbody>
          {issues.map(i => (
            <tr key={i.id}>
              <td><Badge label={i.level} /></td>
              <td><Badge label={i.engine} /></td>
              <td>{i.project}</td>
              <td className="text-xs font-mono">{i.revision}</td>
              <td>{i.author}</td>
              <td>{i.type}</td>
              <td className="text-xs max-w-[200px] truncate">{i.file}</td>
              <td className="max-w-[250px]">{i.desc}</td>
              <td className="max-w-[200px] text-muted text-xs">{i.suggestion}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
