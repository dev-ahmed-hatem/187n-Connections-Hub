/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  // Disable preflight so Tailwind's base reset doesn't fight Ant Design.
  corePlugins: { preflight: false },
  theme: { extend: {} },
  plugins: [],
}
