import type { Inference } from "./Inference";
import type { InferenceContext } from "./InferenceContext";

export interface InferenceEngine {
    infer: (context: InferenceContext) => Promise<readonly Inference[]>;
}
