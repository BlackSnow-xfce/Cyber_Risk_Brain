export const predatorTheme = {
    colors: {
        background: "#0B1220",
        surface: "#111827",
        surfaceLight: "#1F2937",

        border: "#2A3647",

        primary: "#3B82F6",
        primaryHover: "#2563EB",

        success: "#22C55E",
        warning: "#F59E0B",
        danger: "#EF4444",
        info: "#38BDF8",

        text: "#F8FAFC",
        textSecondary: "#94A3B8",
    },

    spacing: {
        xs: 4,
        sm: 8,
        md: 16,
        lg: 24,
        xl: 32,
    },

    radius: {
        sm: 6,
        md: 10,
        lg: 14,
    },

    shadow: {
        panel: "0 6px 18px rgba(0,0,0,0.25)",
    },

    typography: {
        fontFamily:
            "Inter, Segoe UI, Roboto, Helvetica, Arial, sans-serif",

        /*
         * Enterprise Typography
         */

        h1: 24,
        h2: 20,
        h3: 18,
        h4: 16,
        h5: 15,
        h6: 14,

        subtitle: 13,

        body: 13,

        small: 12,

        caption: 11,

        kpi: 38,
    },
} as const;

export type PredatorTheme = typeof predatorTheme;