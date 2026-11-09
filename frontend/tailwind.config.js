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
        gov: {
          navy: '#0b2545',
          dark: '#06182c',
          blue: '#134074',
          accent: '#d97706',
        }
      }
    },
  },
  plugins: [],
}
