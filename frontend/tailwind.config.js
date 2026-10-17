/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: '#060b15',
        surface: {
          DEFAULT: '#0a1120',
          elevated: '#0e172a',
          inset: '#060e1d',
          card: '#0a1120',
          hover: '#111c34',
        },
        border: {
          DEFAULT: '#16233b',
          subtle: '#121b2d',
          active: '#273c66',
        },
        brand: {
          teal: '#14b8a6',
          cyan: '#06b6d4',
          blue: '#3b82f6',
        },
        signal: {
          bullish: '#10b981',
          bearish: '#ef4444',
          neutral: '#8b5cf6',
          noise: '#64748b',
          review: '#f59e0b',
        }
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      boxShadow: {
        'glow-teal': '0 0 20px -3px rgba(20, 184, 166, 0.25)',
        'glow-blue': '0 0 20px -3px rgba(59, 130, 246, 0.3)',
        'glow-green': '0 0 15px -2px rgba(16, 185, 129, 0.3)',
        'card': '0 10px 30px -5px rgba(0, 0, 0, 0.4)',
      }
    },
  },
  plugins: [],
}
