import { ReactNode } from 'react';

interface Props {
  children: ReactNode;
  className?: string;
  title?: string;
}

export function Card({ children, className = '', title }: Props) {
  return (
    <div className={`bg-card border border-[#d8e1ef] rounded-card p-5 shadow-lg ${className}`}>
      {title && <h2 className="text-base font-semibold mb-3 text-gray-700">{title}</h2>}
      {children}
    </div>
  );
}

export function StatsCard({ value, label }: { value: number; label: string }) {
  return (
    <Card>
      <b className="text-4xl block">{value}</b>
      <span className="text-muted text-sm">{label}</span>
    </Card>
  );
}
