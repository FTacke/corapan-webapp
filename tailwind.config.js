const defaultTheme = require('tailwindcss/defaultTheme');

module.exports = {
  content: [
    './templates/**/*.html',
    './static/js/**/*.js',
    './src/**/*.py'
  ],
  theme: {
    extend: {
      colors: {
        brand: { DEFAULT: '#053c96' },
        'brand-ink': '#244652',
        ink: '#414141',
        surface: '#eaf3f5',
        muted: '#a9c9d0',
        hover: '#efede1',
        line: '#2f5f73',
        line2: '#4d4d4d',
        page: '#c7d5d8'
      },
      fontFamily: {
        sans: ['Arial', ...defaultTheme.fontFamily.sans],
        condensed: ['Arial Narrow', 'Helvetica Neue Condensed', 'Arial', 'sans-serif']
      }
    }
  },
  corePlugins: {
    preflight: false
  },
  plugins: []
};
