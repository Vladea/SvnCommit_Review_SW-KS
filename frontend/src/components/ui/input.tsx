import { InputHTMLAttributes } from 'react';

interface Props extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
}

export function Input({ label, className = '', ...props }: Props) {
  return (
    <div className="flex flex-col gap-1">
      {label && <label className="text-xs text-muted font-medium">{label}</label>}
      <input className={`w-full ${className}`} {...props} />
    </div>
  );
}
