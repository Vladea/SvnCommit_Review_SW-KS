'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { AuthorStat } from '@/lib/types';

export default function AuthorsPage() {
  const [authors, setAuthors] = useState<AuthorStat[]>([]);

  useEffect(() => {
    api.get<AuthorStat[]>('/api/authors/latest').then(setAuthors);
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-5">提交人统计（最新报告）</h1>
      <table>
        <thead><tr><th>#</th><th>提交人</th><th>提交次数</th><th>变更文件</th><th>项目数</th><th>P1</th><th>P2</th><th>P3</th><th>P4</th><th>问题密度</th></tr></thead>
        <tbody>
          {authors.map((a, i) => (
            <tr key={a.author}>
              <td className="text-muted">{i + 1}</td>
              <td className="font-medium">{a.author || 'unknown'}</td>
              <td>{a.commit_count}</td>
              <td>{a.file_count}</td>
              <td>{a.project_count}</td>
              <td className="text-danger">{a.p1 || '-'}</td>
              <td className="text-orange-600">{a.p2 || '-'}</td>
              <td className="text-yellow-700">{a.p3 || '-'}</td>
              <td className="text-muted">{a.p4 || '-'}</td>
              <td>{a.density.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
