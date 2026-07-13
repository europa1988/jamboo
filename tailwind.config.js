/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './apps/*/templates/**/*.html',
  ],
  theme: {
    extend: {
      colors: {
        'jamboo-orange': '#ff6b35',
        'jamboo-dark': '#1a1a1b',
        'jamboo-light-gray': '#f6f7f8',
        'jamboo-dark-gray': '#818384',
        'jamboo-blue': '#0079d3',
        'jamboo-card-bg': '#f6f7f8',
        'jamboo-border': '#e5e7eb',
        'jamboo-footer': '#0f172a',
        'jamboo-header-start': '#1a5f9e',
        'jamboo-header-end': '#0a2a5a',
        'dark-bg': '#121212',
        'dark-card': '#1e1e1e',
        'dark-text': '#e0e0e0',
        'dark-border': '#333333',
      },
      borderRadius: {
        'global': '16px',
        'element': '12px',
        'button': '24px',
        'small': '8px'
      }
    },
  },
  plugins: [],
}