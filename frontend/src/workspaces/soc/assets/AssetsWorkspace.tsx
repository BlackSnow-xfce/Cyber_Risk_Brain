import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";

import { useSOCWorkspace } from "../SOCWorkspaceContext";
import AssetDetailsPanel from "./AssetDetailsPanel";
import { assetRepository } from "./MockAssetRepository";
import AssetsList from "./AssetsList";
import AssetsToolbar from "./AssetsToolbar";

export default function AssetsWorkspace() {
    const { selectedAsset, setSelectedAsset } = useSOCWorkspace();
    const assets = assetRepository.getAssets();

    return (
        <Stack spacing={2}>
            <AssetsToolbar />

            <Box
                sx={{
                    display: "grid",
                    gridTemplateColumns: {
                        xs: "minmax(0, 1fr)",
                        xl: "minmax(0, 1.65fr) minmax(320px, 0.75fr)",
                    },
                    gap: 2,
                    alignItems: "start",
                    minWidth: 0,
                }}
            >
                <AssetsList
                    assets={assets}
                    selectedAssetId={selectedAsset?.id ?? null}
                    onSelect={setSelectedAsset}
                />
                <AssetDetailsPanel asset={selectedAsset} />
            </Box>
        </Stack>
    );
}
