'use client';

import { ButtonHTMLAttributes } from 'react';

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'danger' | 'ghost';
  size?: 'sm' | 'md';
}

export function Button({ variant = 'primary', size = 'md', className = '', children, ...props }: Props) {
  const base = 'cursor-pointer border-0 font-medium inline-flex items-center gap-1 transition-colors';
  const variants = {
    primary: 'bg-gradient-to-r from-primary to-primary-light text-white rounded-btn',
    danger: 'bg-danger text-white rounded-btn',
    ghost: 'bg-transparent hover:bg-blue-50 rounded-btn',
  };
  const sizes = { sm: 'px-3 py-1.5 text-xs rounded-lg', md: 'px-5 py-2.5 text-sm rounded-btn' };
  return (
    <button className={`${base} ${variants[variant]} ${sizes[size]} ${className}`} {...props}>
      {children}
    </button>
  );
}
