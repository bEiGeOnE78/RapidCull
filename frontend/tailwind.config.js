/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        surface: '#181818',
        panel: '#222',
        border: '#333',
      },
    },
  },
  plugins: [],
}
