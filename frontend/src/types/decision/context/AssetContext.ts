export interface AssetContext {
    assetId: string;

    name: string;

    type: string;

    owner: string;

    criticality: string;

    internetFacing: boolean;

    operatingSystem?: string;

    location?: string;
}