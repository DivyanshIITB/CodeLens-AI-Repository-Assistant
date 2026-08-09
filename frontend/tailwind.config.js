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
        github: {
          dark: '#0d1117',
          panel: '#161b22',
          border: '#30363d',
          subtle: '#21262d',
          hover: '#30363d',
          text: '#c9d1d9',
          muted: '#8b949e',
          accent: '#58a6ff',
          green: '#238636',
          purple: '#bc8cff',
          yellow: '#d29922',
          red: '#f85149'
        }
      }
    },
  },
  plugins: [],
}
