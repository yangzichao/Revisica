/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: ['./src/renderer/src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        paper: {
          50: '#FEFCF9',
          100: '#FAF6F0',
          200: '#F3EBE0',
          300: '#E8DDD0',
          400: '#D4C5B4',
          500: '#B8A998',
        },
        ink: {
          DEFAULT: '#2C2825',
          secondary: '#5C5248',
          tertiary: '#8A7D6E',
          faint: '#B5A899',
        },
        accent: {
          DEFAULT: '#C67A3C',
          hover: '#B06A2F',
          light: '#D4955E',
        },
        success: '#4A7C59',
        danger: '#A63D2F',
      },
      fontFamily: {
        serif: ["'Source Serif 4'", 'Charter', 'Palatino', 'Georgia', 'serif'],
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        mono: ["'JetBrains Mono'", "'SF Mono'", 'Menlo', 'monospace'],
      },
      boxShadow: {
        subtle: '0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.02)',
        elevated: '0 4px 12px rgba(0,0,0,0.06), 0 1px 3px rgba(0,0,0,0.04)',
      },
    },
  },
  plugins: [require('@tailwindcss/typography')],
}
