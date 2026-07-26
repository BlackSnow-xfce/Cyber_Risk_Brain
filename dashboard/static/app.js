async function loadDashboard() {

    const response = await fetch("/api/dashboard");
    const data = await response.json();

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

    const highest = data.highest_risk;

    const highestRisk = document.getElementById("highestRisk");

    if (highest) {

        highestRisk.innerHTML = `
            <h3>${highest.title}</h3>
            <p><strong>Asset:</strong> ${highest.asset ?? "-"}</p>
            <p><strong>Risk Score:</strong> ${highest.score}</p>
            <p><strong>Risk Level:</strong> ${highest.risk_level}</p>
            <p><strong>CVE:</strong> ${highest.cve ?? "-"}</p>
        `;

    }

    const table = document.getElementById("findingsTable");

    table.innerHTML = "";

    data.findings.forEach(finding => {

        const row = document.createElement("tr");

        row.innerHTML = `
            <td>${finding.asset ?? "-"}</td>
            <td>${finding.title}</td>
            <td>${finding.risk_level}</td>
            <td>${finding.score}</td>
        `;

        table.appendChild(row);

    });

}

loadDashboard();