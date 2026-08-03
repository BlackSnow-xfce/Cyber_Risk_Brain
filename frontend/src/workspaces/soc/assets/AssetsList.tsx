import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import Panel from "@/ui/panel/Panel";

import type { Asset } from "./Asset";
import AssetListItem from "./AssetListItem";

interface AssetsListProps {
    assets: readonly Asset[];
    selectedAssetId: string | null;
    onSelect: (asset: Asset) => void;
}

export default function AssetsList({
    assets,
    selectedAssetId,
    onSelect,
}: AssetsListProps) {
    return (
        <Panel component="section" aria-labelledby="assets-list-title">
            <Stack spacing={2}>
                <Typography
                    id="assets-list-title"
                    variant="h6"
                >
                    Assets List
                </Typography>

                {assets.map((asset) => (
                    <AssetListItem
                        key={asset.id}
                        asset={asset}
                        selected={asset.id === selectedAssetId}
                        onSelect={onSelect}
                    />
                ))}
            </Stack>
        </Panel>
    );
}
