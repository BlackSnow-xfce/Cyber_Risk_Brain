export interface InferenceResult {
    summary: string;
    confidence: number;
    findings: readonly string[];
}
