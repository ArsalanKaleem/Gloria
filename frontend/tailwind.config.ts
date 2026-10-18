import type { Config } from 'tailwindcss';
import { site } from './src/config';

const config: Config = {
  content: [
    './src/app/**/*.{ts,tsx}',
    './src/components/**/*.{ts,tsx}',
    './src/lib/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        gloria: {
          primary: site.brandColor, // set in src/config.ts
          accent: '#D4A017',
        },
      },
    },
  },
  plugins: [],
};

export default config;
