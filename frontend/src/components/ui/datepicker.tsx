'use client';

import { useState, useRef, useEffect } from 'react';

interface DatePickerProps {
  value: string;
  onChange: (val: string) => void;
  label?: string;
  placeholder?: string;
  min?: string;
  max?: string;
}

const WEEKDAYS = ['日', '一', '二', '三', '四', '五', '六'];

export function DatePicker({ value, onChange, label, placeholder = 'YYYY-MM-DD', min = '2020-01-01', max }: DatePickerProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const today = new Date();
  const maxDate = max ? new Date(max) : today;
  const minDate = new Date(min);

  const d = value ? new Date(value + 'T00:00:00') : today;
  if (isNaN(d.getTime())) {
    // if invalid, fall back to showing current month
  }
  const displayDate = !isNaN(d.getTime()) ? d : today;
  const [year, setYear] = useState(displayDate.getFullYear());
  const [month, setMonth] = useState(displayDate.getMonth());

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    if (open) document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [open]);

  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const firstDay = new Date(year, month, 1).getDay();

  const isInRange = (d: number) => {
    const cd = new Date(year, month, d);
    return cd >= minDate && cd <= maxDate;
  };

  const isSelected = (d: number) => {
    const sel = new Date(year, month, d);
    const cur = new Date(value + 'T00:00:00');
    return sel.getTime() === cur.getTime();
  };

  const selectDate = (d: number) => {
    const m = String(month + 1).padStart(2, '0');
    const day = String(d).padStart(2, '0');
    onChange(`${year}-${m}-${day}`);
    setOpen(false);
  };

  const prevMonth = () => {
    if (month === 0) { setMonth(11); setYear(y => y - 1); }
    else setMonth(m => m - 1);
  };
  const nextMonth = () => {
    if (month === 11) { setMonth(0); setYear(y => y + 1); }
    else setMonth(m => m + 1);
  };

  return (
    <div className="relative" ref={ref}>
      {label && <label className="block text-sm text-muted mb-1">{label}</label>}
      <div className="flex items-center gap-1">
        <input
          type="text"
          value={value}
          onChange={e => onChange(e.target.value)}
          placeholder={placeholder}
          className="w-32 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-primary"
        />
        <button
          type="button"
          onClick={() => { setOpen(!open); if (!isNaN(d.getTime())) { setYear(d.getFullYear()); setMonth(d.getMonth()); } }}
          className="p-2 text-muted hover:text-primary hover:bg-gray-100 rounded-lg cursor-pointer"
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><rect x="2" y="3" width="12" height="11" rx="1" stroke="currentColor" strokeWidth="1.5"/><path d="M5 1v3M11 1v3" stroke="currentColor" strokeWidth="1.5"/><path d="M2 6h12" stroke="currentColor" strokeWidth="1.5"/></svg>
        </button>
      </div>

      {open && (
        <div className="absolute z-50 mt-1 bg-white border border-gray-200 rounded-xl shadow-lg p-3 w-64">
          <div className="flex items-center justify-between mb-2">
            <button onClick={() => setYear(y => y - 1)} title="上一年" className="px-1 text-gray-400 hover:text-primary text-sm">◀◀</button>
            <button onClick={prevMonth} title="上一月" className="px-2 text-gray-400 hover:text-primary text-sm font-bold">◀</button>
            <span className="text-sm font-medium min-w-[100px] text-center">{year}年{month + 1}月</span>
            <button onClick={nextMonth} title="下一月" className="px-2 text-gray-400 hover:text-primary text-sm font-bold">▶</button>
            <button onClick={() => setYear(y => y + 1)} title="下一年" className="px-1 text-gray-400 hover:text-primary text-sm">▶▶</button>
          </div>
          <div className="grid grid-cols-7 gap-0 text-center text-xs">
            {WEEKDAYS.map(w => <div key={w} className="py-1 text-muted font-medium">{w}</div>)}
            {Array.from({ length: firstDay }, (_, i) => <div key={'e' + i} />)}
            {Array.from({ length: daysInMonth }, (_, i) => {
              const day = i + 1;
              const inRange = isInRange(day);
              const selected = isSelected(day);
              return (
                <button
                  key={day}
                  disabled={!inRange}
                  onClick={() => selectDate(day)}
                  className={`w-8 h-8 text-xs rounded-full flex items-center justify-center cursor-pointer
                    ${selected ? 'bg-primary text-white font-bold' : ''}
                    ${!selected && inRange ? 'hover:bg-blue-50' : ''}
                    ${!inRange ? 'text-gray-300 cursor-default' : ''}
                  `}
                >
                  {day}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
