function renderSummary(data) {

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
            ...data.findings.map(
                finding => finding.score
            )
        );

    }

    const risk =
        document.getElementById(
            "overallRiskScore"
        );

    if (risk)
        risk.textContent = highestScore;

    //--------------------------------------------------
    // Decision Count
    //--------------------------------------------------

    const decisionCount =
        document.getElementById(
            "decisionCount"
        );

    if (decisionCount)
        decisionCount.textContent =
            data.findings.length;

}
