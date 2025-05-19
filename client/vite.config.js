import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";
import runtimeErrorOverlay from "@replit/vite-plugin-runtime-error-modal";

export default defineConfig({
  plugins: [
    react(),
    runtimeErrorOverlay(),
    ...(process.env.NODE_ENV !== "production" &&
    process.env.REPL_ID !== undefined
      ? [
          await import("@replit/vite-plugin-cartographer").then((m) =>
            m.cartographer(),
          ),
        ]
      : []),
  ],
  resolve: {
    alias: {
      // Core app aliases
      "@": path.resolve(__dirname, "src"),
      "@components": path.resolve(__dirname, "src/components"),
      "@hooks": path.resolve(__dirname, "src/hooks"),
      "@lib": path.resolve(__dirname, "src/lib"),
      "@pages": path.resolve(__dirname, "src/pages"),
      "@types": path.resolve(__dirname, "src/types"),
      "@services": path.resolve(__dirname, "src/services"),

      // Server side paths (if applicable)
      "@server": path.resolve(__dirname, "../server"),
      "@shared": path.resolve(__dirname, "../shared"),

      // Assets
      "@assets": path.resolve(__dirname, "../attached_assets"),
    },
  },
  // Define environment variable handling
  define: {
    // This ensures process.env can be used if needed
    "process.env": {},
  },
  root: path.resolve(__dirname),
  build: {
    outDir: path.resolve(__dirname, "../dist/public"),
    emptyOutDir: true,
  },
  // Serve configuration for development
  server: {
    port: 3000,
    host: "0.0.0.0", // Required to access from outside
    proxy: {
      // Proxy API requests to your backend server
      "/api": {
        target: "http://localhost:5000",
        changeOrigin: true,
      },
    },
  },
  // Set the entry point to index.js
  optimizeDeps: {
    entries: ["./src/index.jsx"],
  },
});
