async function loadDashboard() {

    const response = await fetch("/api/dashboard");

    const data = await response.json();

    //--------------------------------------------------
    // Summary
    //--------------------------------------------------

    document.getElementById("total").textContent =
        data.summary.total_findings;

    document.getElementById("critical").textContent =
        data.summary.critical;

    document.getElementById("high").textContent =
        data.summary.high;

    document.getElementById("medium").textContent =
        data.summary.medium;

    document.getElementById("low").textContent =
        data.summary.low;

    //--------------------------------------------------
    // Overall Risk
    //--------------------------------------------------

    let highestScore = 0;

    if (data.findings.length > 0) {

        highestScore = Math.max(
            ...data.findings.map(f => f.score)
        );

    }

    const risk =
        document.getElementById("overallRiskScore");

    if (risk)
        risk.textContent = highestScore;

    //--------------------------------------------------
    // Decision Count
    //--------------------------------------------------

    const decisionCount =
        document.getElementById("decisionCount");

    if (decisionCount)
        decisionCount.textContent =
            data.findings.length;

    //--------------------------------------------------
    // Highest Risk Card
    //--------------------------------------------------

    const highest =
        data.highest_risk;

    const highestRisk =
        document.getElementById("highestRisk");

    if (highestRisk && highest) {

        highestRisk.innerHTML = `

<h2>${highest.title}</h2>

<br>

<p><strong>Asset</strong></p>

<p>${highest.asset ?? "-"}</p>

<br>

<p><strong>Risk</strong></p>

<h1>${highest.score}</h1>

<br>

<p><strong>Level</strong></p>

<p>${highest.risk_level}</p>

<br>

<p><strong>CVE</strong></p>

<p>${highest.cve ?? "-"}</p>

`;

    }

    //--------------------------------------------------
    // Decision Feed
    //--------------------------------------------------

    const feed =
        document.querySelector(".feed");

    if (feed) {

        feed.innerHTML = "";

        data.findings
            .slice(0, 5)
            .forEach(finding => {

                feed.innerHTML += `

<div class="feed-item">

<div class="feed-time">

LIVE

</div>

<div>

<strong>${finding.title}</strong>

<br>

${finding.risk_level} • ${finding.score}

</div>

</div>

`;

            });

    }

    //--------------------------------------------------
    // Decision Table
    //--------------------------------------------------

    const table =
        document.getElementById("findingsTable");

    table.innerHTML = "";

    data.findings.forEach(finding => {

        table.innerHTML += `

<tr>

<td>${finding.title}</td>

<td>${finding.risk_level}</td>

<td>${finding.score}</td>

<td>Monitor</td>

</tr>

`;

    });

    //--------------------------------------------------
    // Graph
    //--------------------------------------------------

    const graph =
        document.getElementById("graphSummary");

    if (graph)
        graph.textContent =
            JSON.stringify(
                data.graph ?? {},
                null,
                2
            );

    //--------------------------------------------------
    // Team Risk
    //--------------------------------------------------

    const team =
        document.getElementById("teamRisk");

    if (team)
        team.textContent =
            JSON.stringify(
                data.team_risk ?? {},
                null,
                2
            );

    //--------------------------------------------------
    // Reports
    //--------------------------------------------------

    const reports =
        document.getElementById("reports");

    if (reports)
        reports.textContent =
            JSON.stringify(
                data.reports ?? {},
                null,
                2
            );

    //--------------------------------------------------
    // Story Bundles
    //--------------------------------------------------

    const stories =
        document.getElementById("storyBundles");

    if (stories)
        stories.textContent =
            JSON.stringify(
                data.story_bundles ?? {},
                null,
                2
            );

}

loadDashboard();