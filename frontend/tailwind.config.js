/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          dark: '#0a0a0f',
          card: '#111118',
          border: '#1e1e2e',
        },
      },
    },
  },
  plugins: [],
}
