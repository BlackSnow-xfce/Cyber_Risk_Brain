function getElement(id) {

    return document.getElementById(id);

}


function setText(id, value) {

    const element = getElement(id);

    if (element) {

        element.textContent = value ?? "-";

    }

}


function escapeHtml(value) {

    return String(value ?? "")

        .replaceAll("&", "&amp;")

        .replaceAll("<", "&lt;")

        .replaceAll(">", "&gt;")

        .replaceAll('"', "&quot;")

        .replaceAll("'", "&#039;");

}


function formatLabel(value) {

    return String(value ?? "-")

        .replaceAll("_", " ")

        .replace(/\b\w/g, c => c.toUpperCase());

}


function getRiskScore(decision) {

    const value = Number(

        decision?.risk_score

        ?? decision?.metadata?.risk_score

        ?? 0

    );

    return Number.isFinite(value)

        ? value

        : 0;

}


function getConfidence(decision) {

    const value = Number(

        decision?.confidence?.score

        ?? 0

    );

    return Number.isFinite(value)

        ? value

        : 0;

}


function countPriorities(decisions) {

    const result = {

        critical: 0,

        high: 0,

        medium: 0,

        low: 0,

        informational: 0,

    };

    decisions.forEach(decision => {

        const priority = (

            decision.priority || "informational"

        ).toLowerCase();

        if (result.hasOwnProperty(priority)) {

            result[priority]++;

        }

    });

    return result;

}


function highestDecision(decisions) {

    if (decisions.length === 0) {

        return null;

    }

    return decisions.reduce(

        (best, current) =>

            getRiskScore(current) >

            getRiskScore(best)

                ? current

                : best

    );

}


function renderSummary(data) {

    const decisions = data.decisions || [];

    const counts = countPriorities(

        decisions

    );

    setText(

        "total",

        decisions.length

    );

    setText(

        "critical",

        counts.critical

    );

    setText(

        "high",

        counts.high

    );

    setText(

        "medium",

        counts.medium

    );

    setText(

        "low",

        counts.low + counts.informational

    );

}


function renderHighestRisk(decisions) {

    const container =

        getElement("highestRisk");

    if (!container) {

        return;

    }

    const highest =

        highestDecision(decisions);

    if (!highest) {

        container.innerHTML =

            "<p>No findings.</p>";

        return;

    }

    const recommendation =

        highest.recommendations?.[0];

    container.innerHTML = `

<h3>${escapeHtml(highest.finding_id)}</h3>

<p><strong>Priority:</strong>

${formatLabel(highest.priority)}</p>

<p><strong>Risk Score:</strong>

${getRiskScore(highest)}/100</p>

<p><strong>Confidence:</strong>

${getConfidence(highest).toFixed(0)}%</p>

<p><strong>Action:</strong>

${formatLabel(highest.action)}</p>

<p><strong>Decision:</strong>

${escapeHtml(highest.decision)}</p>

<p><strong>Business Impact:</strong>

${escapeHtml(

highest.business_impact.summary

)}</p>

<p><strong>Top Recommendation:</strong>

${escapeHtml(

recommendation?.title ?? "-"

)}</p>

`;

}

function renderDecisionTable(decisions) {

    const table = getElement(
        "findingsTable"
    );

    if (!table) {

        return;

    }

    table.innerHTML = "";

    decisions.forEach(decision => {

        const row = document.createElement(
            "tr"
        );

        row.innerHTML = `

<td>${escapeHtml(
decision.finding_id
)}</td>

<td>${escapeHtml(
formatLabel(decision.priority)
)}</td>

<td>${getRiskScore(
decision
)}</td>

<td>${escapeHtml(
formatLabel(decision.action)
)}</td>

`;

        table.appendChild(
            row
        );

    });

    if (decisions.length === 0) {

        const row =
            document.createElement("tr");

        row.innerHTML = `

<td colspan="4">

No findings available.

</td>

`;

        table.appendChild(row);

    }

}


function renderAdditionalData(data) {

    const graphSummary =
        getElement("graphSummary");

    if (graphSummary) {

        graphSummary.textContent =
            JSON.stringify(

                data.graph_summary,

                null,

                2

            );

    }

    const teamRisk =
        getElement("teamRisk");

    if (teamRisk) {

        teamRisk.textContent =
            JSON.stringify(

                data.team_risk,

                null,

                2

            );

    }

    const reports =
        getElement("reports");

    if (reports) {

        reports.textContent =
            JSON.stringify(

                data.reports,

                null,

                2

            );

    }

    const stories =
        getElement("storyBundles");

    if (stories) {

        stories.textContent =
            JSON.stringify(

                data.story_bundles,

                null,

                2

            );

    }

}

function renderError(message) {

    const container =
        getElement("highestRisk");

    if (!container) {

        return;

    }

    container.innerHTML = `

<p>

<strong>Dashboard Error:</strong>

${escapeHtml(message)}

</p>

`;

}


async function loadDashboard() {

    try {

        const response = await fetch(
            "/api/dashboard"
        );

        if (!response.ok) {

            throw new Error(

                `HTTP ${response.status}`

            );

        }

        const data =
            await response.json();

        const decisions =
            data.decisions ?? [];

        renderSummary(
            data
        );

        renderHighestRisk(
            decisions
        );

        renderDecisionTable(
            decisions
        );

        renderAdditionalData(
            data
        );

    }

    catch (error) {

        console.error(error);

        renderError(

            error.message ??

            "Unknown Error"

        );

    }

}


document.addEventListener(

    "DOMContentLoaded",

    () => {

        loadDashboard();

    }

);
