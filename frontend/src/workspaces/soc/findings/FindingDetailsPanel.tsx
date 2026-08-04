import Divider from "@mui/material/Divider";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import {
    ExecutionTrace,
    ExplainabilityPipeline,
} from "@/components/reasoning";
import {
    knowledgeBindingRepository,
    knowledgeRepository,
} from "@/knowledge";
import { defaultReasoningOrchestrator } from "@/reasoning/DefaultReasoningOrchestrator";
import Panel from "@/ui/panel/Panel";

import type { Finding } from "./Finding";

interface FindingDetailsPanelProps {
    finding: Finding | null;
}

export default function FindingDetailsPanel({
    finding,
}: FindingDetailsPanelProps) {
    const detailSections = finding
        ? [
              ["Explainability", finding.explainability.reason],
              [
                  "Evidence",
                  finding.evidence
                      .map(
                          (evidence) =>
                              `${evidence.title}: ${evidence.description}`,
                      )
                      .join("; "),
              ],
              ["Recommendations", finding.recommendation.description],
          ] as const
        : [];
    const knowledgeBindings = finding
        ? knowledgeBindingRepository.getBindingsByEntityId(finding.id)
        : [];
    const relevantKnowledgeIds = new Set(
        knowledgeBindings.map((binding) => binding.knowledgeItemId),
    );
    const knowledge = knowledgeRepository
        .getKnowledgeItems()
        .filter((item) => relevantKnowledgeIds.has(item.id));
    const reasoningSession = finding
        ? defaultReasoningOrchestrator.execute({
              entity: finding,
              knowledge,
              knowledgeBindings,
              evidence: finding.evidence,
              correlations: finding.correlations,
          })
        : null;

    return (
        <Panel
            component="aside"
            aria-labelledby="finding-details-title"
            sx={{ height: "100%" }}
        >
            <Stack spacing={2}>
                <Typography
                    id="finding-details-title"
                    variant="h6"
                >
                    Finding Details
                </Typography>

                <Typography
                    variant="body2"
                    color="text.secondary"
                >
                    {finding
                        ? finding.title
                        : "Select a finding to review its details."}
                </Typography>

                <Divider />

                {finding && (
                    <Stack spacing={0.5}>
                        <Typography variant="subtitle2">
                            Executive Summary
                        </Typography>
                        <Typography
                            variant="body2"
                            color="text.secondary"
                        >
                            {finding.description}
                        </Typography>
                    </Stack>
                )}

                {finding && (
                    <ExplainabilityPipeline
                        entity={finding}
                        knowledge={knowledge}
                        knowledgeBindings={knowledgeBindings}
                    />
                )}

                {reasoningSession?.result && (
                    <ExecutionTrace
                        trace={reasoningSession.result.executionTrace}
                    />
                )}

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
