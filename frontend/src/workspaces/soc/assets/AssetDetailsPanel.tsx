import Divider from "@mui/material/Divider";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import Panel from "@/ui/panel/Panel";

import type { Asset } from "./Asset";

interface AssetDetailsPanelProps {
    asset: Asset | null;
}

export default function AssetDetailsPanel({
    asset,
}: AssetDetailsPanelProps) {
    const detailSections = asset
        ? [
              ["Asset Overview", asset.description],
              ["Business Context", asset.businessContext],
              ["Related Findings", asset.relatedFindings],
              ["Related Investigations", asset.relatedInvestigations],
              ["Vulnerabilities", asset.vulnerabilities],
              ["Recommended Actions", asset.recommendation.description],
          ] as const
        : [];

    return (
        <Panel
            component="aside"
            aria-labelledby="asset-details-title"
            sx={{ height: "100%" }}
        >
            <Stack spacing={2}>
                <Typography
                    id="asset-details-title"
                    variant="h6"
                >
                    Asset Details
                </Typography>

                <Typography
                    variant="body2"
                    color="text.secondary"
                >
                    {asset
                        ? asset.title
                        : "Select an asset to review its details."}
                </Typography>

                <Divider />

                {detailSections.map(([section, content]) => (
                    <Stack key={section} spacing={0.5}>
                        <Typography variant="subtitle2">
                            {section}
                        </Typography>

                        <Typography
                            variant="body2"
                            color="text.secondary"
                        >
                            {content}
                        </Typography>
                    </Stack>
                ))}
            </Stack>
        </Panel>
    );
}
