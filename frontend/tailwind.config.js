/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: { DEFAULT: '#2563eb', light: '#3b82f6', dark: '#1d4ed8' },
        sidebar: '#f8fbff',
        card: '#ffffffcc',
        danger: '#ef4444',
        warning: '#f59e0b',
        info: '#3b82f6',
        muted: '#64748b',
      },
      borderRadius: { card: '18px', btn: '10px' },
    },
  },
  plugins: [],
};
