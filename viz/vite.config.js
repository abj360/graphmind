#!/usr/bin/env node
/**
 * vite.config.js --- vite build configuration for the viewer
 *  *
 *  * Contains:
 *  *   config export with dev proxy
 */

import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

/**
 * Vite configuration: React plugin plus an API proxy for local dev.
 */
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: process.env.VITE_API_BASE_URL ?? "http://localhost:4000",
        changeOrigin: true,
      },
    },
  },
});
