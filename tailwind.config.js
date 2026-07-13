/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './apps/*/templates/**/*.html',
  ],
  theme: {
    extend: {
      colors: {
        'jamboo-orange': '#FF6B35',
        'jamboo-dark-gray': '#6B7280',
        'dark-card': '#1F2937',
        'dark-text': '#F3F4F6',
      },
      borderRadius: {
        'global': '12px',
        'small': '8px',
      }
    },
  },
  plugins: [],
}