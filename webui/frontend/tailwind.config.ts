import type { Config } from "tailwindcss";
import { nextui } from "@nextui-org/react";
/** @type {import('tailwindcss').Config} */

module.exports = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
    "./node_modules/@nextui-org/theme/dist/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "gradient-conic":
          "conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))",
        "circle-purple": "url('./image/purple_circle_bg.jpg')",
      },
      dropShadow: {
        input: "1px 0px 6px #aa00ff",
      },
    },
  },
  plugins: [nextui()],
};