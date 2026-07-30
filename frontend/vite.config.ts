import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
    plugins: [react()],

    resolve: {
        alias: {
            "@": new URL("./src", import.meta.url).pathname,
            "@app": new URL("./src/app", import.meta.url).pathname,
            "@components": new URL("./src/components", import.meta.url).pathname,
            "@layouts": new URL("./src/layouts", import.meta.url).pathname,
            "@navigation": new URL("./src/navigation", import.meta.url).pathname,
            "@pages": new URL("./src/pages", import.meta.url).pathname,
            "@router": new URL("./src/router", import.meta.url).pathname,
            "@services": new URL("./src/services", import.meta.url).pathname,
            "@theme": new URL("./src/theme", import.meta.url).pathname,
            "@widgets": new URL("./src/widgets", import.meta.url).pathname,
            "@workspaces": new URL("./src/workspaces", import.meta.url).pathname,
        },
    },

    server: {
        port: 5173,
        open: true,
    },
});