import {
    createContext,
    useContext,
    useMemo,
    useState,
    type PropsWithChildren,
} from "react";

import type { Asset } from "./assets/Asset";
import type { Exposure } from "./exposure/Exposure";
import type { Finding } from "./findings/Finding";
import type { Investigation } from "./investigations/Investigation";
import type { ThreatIntelligence } from "./threat-intelligence/ThreatIntelligence";

interface SOCWorkspaceContextValue {
    selectedFinding: Finding | null;
    setSelectedFinding: (finding: Finding) => void;
    selectedAsset: Asset | null;
    setSelectedAsset: (asset: Asset) => void;
    selectedInvestigation: Investigation | null;
    setSelectedInvestigation: (investigation: Investigation) => void;
    selectedThreatIntelligence: ThreatIntelligence | null;
    setSelectedThreatIntelligence: (threat: ThreatIntelligence) => void;
    selectedExposure: Exposure | null;
    setSelectedExposure: (exposure: Exposure) => void;
}

const SOCWorkspaceContext =
    createContext<SOCWorkspaceContextValue | null>(null);

export function SOCWorkspaceProvider({
    children,
}: PropsWithChildren) {
    const [selectedFinding, setSelectedFinding] =
        useState<Finding | null>(null);
    const [selectedAsset, setSelectedAsset] =
        useState<Asset | null>(null);
    const [selectedInvestigation, setSelectedInvestigation] =
        useState<Investigation | null>(null);
    const [selectedThreatIntelligence, setSelectedThreatIntelligence] =
        useState<ThreatIntelligence | null>(null);
    const [selectedExposure, setSelectedExposure] =
        useState<Exposure | null>(null);

    const value = useMemo(
        () => ({
            selectedFinding,
            setSelectedFinding,
            selectedAsset,
            setSelectedAsset,
            selectedInvestigation,
            setSelectedInvestigation,
            selectedThreatIntelligence,
            setSelectedThreatIntelligence,
            selectedExposure,
            setSelectedExposure,
        }),
        [
            selectedFinding,
            selectedAsset,
            selectedInvestigation,
            selectedThreatIntelligence,
            selectedExposure,
        ],
    );

    return (
        <SOCWorkspaceContext.Provider value={value}>
            {children}
        </SOCWorkspaceContext.Provider>
    );
}

export function useSOCWorkspace() {
    const context = useContext(SOCWorkspaceContext);

    if (!context) {
        throw new Error(
            "useSOCWorkspace must be used within a SOCWorkspaceProvider.",
        );
    }

    return context;
}
