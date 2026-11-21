import type { Config } from "tailwindcss";
import preset from "./src/ui/tailwind-preset";

export default {
  presets: [preset],
  content: ["./src/**/*.{ts,tsx}"],
} satisfies Config;
