const colors: Record<string, string> = {
  P1: 'bg-danger/15 text-danger',
  P2: 'bg-orange-100 text-orange-600',
  P3: 'bg-yellow-100 text-yellow-700',
  P4: 'bg-gray-100 text-gray-500',
  rule: 'bg-blue-50 text-blue-600',
  llm: 'bg-purple-50 text-purple-600',
};

export function Badge({ label }: { label: string }) {
  const cls = colors[label] || 'bg-gray-100 text-gray-500';
  return <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${cls}`}>{label}</span>;
}
