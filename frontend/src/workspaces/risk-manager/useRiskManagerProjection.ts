import { useCallback, useEffect, useState } from "react";

import { loadRiskManagerProjection, type RiskManagerProjection } from "./RiskManagerProjection";

export interface RiskManagerProjectionState {
    projection: RiskManagerProjection | null;
    loading: boolean;
    error: string | null;
    reload: () => void;
}

export function useRiskManagerProjection(): RiskManagerProjectionState {
    const [projection, setProjection] = useState<RiskManagerProjection | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [reloadToken, setReloadToken] = useState(0);

    const reload = useCallback(() => setReloadToken((value) => value + 1), []);

    useEffect(() => {
        let cancelled = false;
        setLoading(true);
        setError(null);

        void loadRiskManagerProjection()
            .then((next) => {
                if (!cancelled) setProjection(next);
            })
            .catch((reason: unknown) => {
                if (!cancelled) {
                    setProjection(null);
                    setError(reason instanceof Error ? reason.message : "Risk Manager data could not be loaded.");
                }
            })
            .finally(() => {
                if (!cancelled) setLoading(false);
            });

        return () => {
            cancelled = true;
        };
    }, [reloadToken]);

    return { projection, loading, error, reload };
}
