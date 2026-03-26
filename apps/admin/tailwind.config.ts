import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './features/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        // גופן Rubik לתמיכה בעברית ו-RTL
        rubik: ['Rubik', 'sans-serif'],
      },
    },
  },
  plugins: [],
}

export default config
