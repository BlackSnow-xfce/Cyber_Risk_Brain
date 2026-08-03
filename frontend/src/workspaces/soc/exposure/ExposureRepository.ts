import type { Exposure } from "./Exposure";

export interface ExposureRepository {
    getExposures: () => readonly Exposure[];
}
