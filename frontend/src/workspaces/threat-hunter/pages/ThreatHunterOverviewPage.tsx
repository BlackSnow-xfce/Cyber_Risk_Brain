import { useEffect, useState, type ReactNode } from "react";
import Button from "@mui/material/Button";
import Typography from "@mui/material/Typography";
import { Link } from "react-router-dom";

import type { HuntHypothesis } from "../HuntHypothesis";
import { getHuntHypotheses } from "../HuntHypothesisApiClient";
import "./ThreatHunterOverviewPage.css";

type HypothesisState =
    | { status: "loading" }
    | { status: "error" }
    | { status: "loaded"; hypotheses: HuntHypothesis[] };

interface OperationalCardProps {
    title: string;
    children: ReactNode;
}

function OperationalCard({ title, children }: OperationalCardProps) {
    return (
        <article className="threat-hunter-overview__card">
            <Typography component="h3" className="threat-hunter-overview__card-title">
                {title}
            </Typography>
            <div className="threat-hunter-overview__card-stage">{children}</div>
        </article>
    );
}

export default function ThreatHunterOverviewPage() {
    const [hypothesisState, setHypothesisState] = useState<HypothesisState>({
        status: "loading",
    });

    useEffect(() => {
        let active = true;

        void getHuntHypotheses()
            .then((hypotheses) => {
                if (active) setHypothesisState({ status: "loaded", hypotheses });
            })
            .catch(() => {
                if (active) setHypothesisState({ status: "error" });
            });

        return () => {
            active = false;
        };
    }, []);

    return (
        <main className="threat-hunter-overview">
            <header className="threat-hunter-overview__header">
                <Typography component="p" className="threat-hunter-overview__overline">
                    Proactive discovery workspace
                </Typography>
                <Typography component="h1" className="threat-hunter-overview__title">
                    Threat Hunter Mission Console
                </Typography>
                <Typography component="p" className="threat-hunter-overview__description">
                    Develop hypotheses, prepare queries and maintain entity context
                    without interrupting the operational SOC workflow. Hunting data
                    sources are not connected in this foundation.
                </Typography>
            </header>

            <section aria-labelledby="hunt-work-area-title">
                <Typography component="h2" id="hunt-work-area-title" className="threat-hunter-overview__section-title">
                    Hunt work area
                </Typography>

                <div className="threat-hunter-overview__cards">
                    <OperationalCard title="Active Hunts">
                        <Typography component="p" className="threat-hunter-overview__state-label">
                            Not connected
                        </Typography>
                        <Typography component="p" className="threat-hunter-overview__state-copy">
                            No active hunts are available.
                        </Typography>
                        <Typography component="p" className="threat-hunter-overview__state-detail">
                            Hunting data sources are not connected.
                        </Typography>
                        <Button component={Link} to="/threat-hunting/hunts" variant="outlined" className="threat-hunter-overview__action">
                            View hunts
                        </Button>
                    </OperationalCard>

                    <OperationalCard title="Hunt Hypotheses">
                        <HypothesisCardState state={hypothesisState} />
                        <Button component={Link} to="/threat-hunting/hypotheses" variant="outlined" className="threat-hunter-overview__action">
                            Open hypotheses
                        </Button>
                    </OperationalCard>
                </div>
            </section>
        </main>
    );
}

function HypothesisCardState({ state }: { state: HypothesisState }) {
    if (state.status === "loading") {
        return (
            <Typography component="p" role="status" className="threat-hunter-overview__state-label">
                Loading persisted hypotheses…
            </Typography>
        );
    }

    if (state.status === "error") {
        return (
            <>
                <Typography component="p" role="alert" className="threat-hunter-overview__state-label">
                    Repository unavailable
                </Typography>
                <Typography component="p" className="threat-hunter-overview__state-copy">
                    Persisted hunt hypotheses could not be loaded.
                </Typography>
            </>
        );
    }

    if (state.hypotheses.length === 0) {
        return (
            <>
                <Typography component="p" className="threat-hunter-overview__state-label">
                    No data
                </Typography>
                <Typography component="p" className="threat-hunter-overview__state-copy">
                    No persisted hunt hypotheses are available.
                </Typography>
            </>
        );
    }

    return (
        <>
            <Typography component="p" className="threat-hunter-overview__hypothesis-count">
                {state.hypotheses.length}
            </Typography>
            <Typography component="p" className="threat-hunter-overview__state-copy">
                {state.hypotheses.length === 1
                    ? "Persisted hunt hypothesis"
                    : "Persisted hunt hypotheses"}
            </Typography>
        </>
    );
}
