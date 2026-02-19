/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                official: {
                    950: '#0b1120',
                    900: '#111827', // Primary Text
                    800: '#1f2937',
                    700: '#374151',
                    600: '#4b5563', // Secondary Text
                    500: '#6b7280',
                    400: '#9ca3af',
                    300: '#d1d5db', // Borders
                    200: '#e5e7eb',
                    100: '#f3f4f6', // Light Backgrounds
                    50: '#f9fafb',
                },
                brand: {
                    DEFAULT: '#003366', // Official Government Blue
                    light: '#2563eb',
                    dark: '#1e3a8a',
                },
            },
            fontFamily: {
                sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
                display: ['Inter', 'system-ui', 'sans-serif'],
            },
        },
    },
    plugins: [],
}
