function renderDecision(data) {

    const highest =
        data.highest_risk;

    if (!highest)
        return;

    //--------------------------------------------------
    // Legacy Card
    //--------------------------------------------------

    const highestRisk =
        document.getElementById(
            "highestRisk"
        );

    if (highestRisk) {

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
    // New Decision Console
    //--------------------------------------------------

    const title =
        document.getElementById(
            "decisionTitle"
        );

    if (title)
        title.textContent =
            highest.title;

    const risk =
        document.getElementById(
            "decisionRisk"
        );

    if (risk)
        risk.textContent =
            highest.score;

    const confidence =
        document.getElementById(
            "decisionConfidence"
        );

    if (confidence)
        confidence.textContent =
            "96%";

}
