import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

export default defineConfig({
    plugins: [react()],

    resolve: {
        alias: {
            "@": path.resolve(__dirname, "./src"),
            "@app": path.resolve(__dirname, "./src/app"),
            "@components": path.resolve(__dirname, "./src/components"),
            "@layouts": path.resolve(__dirname, "./src/layouts"),
            "@navigation": path.resolve(__dirname, "./src/navigation"),
            "@pages": path.resolve(__dirname, "./src/pages"),
            "@router": path.resolve(__dirname, "./src/router"),
            "@services": path.resolve(__dirname, "./src/services"),
            "@theme": path.resolve(__dirname, "./src/theme"),
            "@widgets": path.resolve(__dirname, "./src/widgets"),
            "@workspaces": path.resolve(__dirname, "./src/workspaces")
        }
    },

    server: {
        port: 5173,
        open: true
    }
});
