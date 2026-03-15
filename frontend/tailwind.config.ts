import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        'aura-cream': '#FAF7F2',
        'aura-surface': '#EDE8E0',
        'aura-blush': '#D4A89A',
        'aura-brown': '#2C2420',
        'aura-muted': '#8C7B74',
        'aura-gold': '#C9A96E',
        'aura-rust': '#B85C38',
        'aura-sage': '#7A9E7E',
        'aura-white': '#FFFDF9',
      },
      fontFamily: {
        display: ['"Cormorant Garamond"', 'serif'],
        body: ['"DM Sans"', 'sans-serif'],
      },
      keyframes: {
        'fade-in': {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        'fade-in': 'fade-in 0.4s ease-out forwards',
      },
    },
  },
  plugins: [],
}

export default config
