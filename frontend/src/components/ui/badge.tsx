  const colors: Record<string, string> = {
    P1: 'bg-red-100 text-red-600',
    P2: 'bg-orange-100 text-orange-600',
    P3: 'bg-yellow-100 text-yellow-600',
    P4: 'bg-blue-100 text-blue-600',
    rule: 'bg-purple-100 text-purple-600',
    llm: 'bg-teal-100 text-teal-600',
    OK: 'bg-green-100 text-green-600',
    FAIL: 'bg-red-100 text-red-600',
  };

export function Badge({ label }: { label: string }) {
  const cls = colors[label] || 'bg-gray-100 text-gray-500';
  return <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${cls}`}>{label}</span>;
}
