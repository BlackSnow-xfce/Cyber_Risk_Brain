import { CssBaseline, ThemeProvider, createTheme } from "@mui/material";
import type { ReactNode } from "react";

import { predatorTheme } from "./predatorTheme";

const theme = createTheme({
    palette: {
        mode: "dark",

        primary: {
            main: predatorTheme.colors.primary,
        },

        background: {
            default: predatorTheme.colors.background,
            paper: predatorTheme.colors.surface,
        },

        text: {
            primary: predatorTheme.colors.text,
            secondary: predatorTheme.colors.textSecondary,
        },
    },

    shape: {
        borderRadius: predatorTheme.radius.md,
    },

    typography: {
        fontFamily: predatorTheme.typography.fontFamily,

        h1: {
            fontSize: "2rem",
            fontWeight: 700,
        },

        h2: {
            fontSize: "1.625rem",
            fontWeight: 700,
        },

        h3: {
            fontSize: "1.375rem",
            fontWeight: 600,
        },

        h4: {
            fontSize: "1.25rem",
            fontWeight: 600,
        },

        h5: {
            fontSize: "1rem",
            fontWeight: 600,
        },

        h6: {
            fontSize: "0.9rem",
            fontWeight: 600,
        },

        subtitle1: {
            fontSize: "0.875rem",
            fontWeight: 500,
        },

        subtitle2: {
            fontSize: "0.8125rem",
            fontWeight: 500,
        },

        body1: {
            fontSize: "0.875rem",
            lineHeight: 1.6,
        },

        body2: {
            fontSize: "0.8125rem",
            lineHeight: 1.6,
        },

        caption: {
            fontSize: "0.75rem",
            letterSpacing: "0.04em",
        },

        overline: {
            fontSize: "0.6875rem",
            letterSpacing: "0.12em",
            fontWeight: 600,
        },

        button: {
            fontSize: "0.875rem",
            fontWeight: 600,
            textTransform: "none",
        },
    },

    components: {
        MuiPaper: {
            styleOverrides: {
                root: {
                    backgroundImage: "none",
                },
            },
        },
    },
});

interface Props {
    children: ReactNode;
}

export default function PredatorThemeProvider({
    children,
}: Props) {
    return (
        <ThemeProvider theme={theme}>
            <CssBaseline />
            {children}
        </ThemeProvider>
    );
}