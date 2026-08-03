import type { Asset } from "./Asset";

export interface AssetRepository {
    getAssets: () => readonly Asset[];
}
