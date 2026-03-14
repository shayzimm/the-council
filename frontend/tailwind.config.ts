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
        'aura-white': '#FFFDF9',
      },
      fontFamily: {
        display: ['"Cormorant Garamond"', 'serif'],
        body: ['"DM Sans"', 'sans-serif'],
      },
    },
  },
  plugins: [],
}

export default config
