import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  base: "/fantasy-role-ai/",
  plugins: [react()],
});
