import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";

import App from "./App";
import PredatorThemeProvider from "./ui/theme/PredatorThemeProvider";

import "./styles/global.css";

ReactDOM.createRoot(
    document.getElementById("root") as HTMLElement
).render(
    <React.StrictMode>
        <PredatorThemeProvider>
            <BrowserRouter>
                <App />
            </BrowserRouter>
        </PredatorThemeProvider>
    </React.StrictMode>
);