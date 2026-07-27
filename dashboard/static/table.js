function renderTable(data){

    const table =
        document.getElementById(
            "findingsTable"
        );

    if(!table)
        return;

    table.innerHTML="";

    data.findings.forEach(

        finding=>{

            table.innerHTML+=`

<tr>

<td>${finding.title}</td>

<td>${finding.risk_level}</td>

<td>${finding.score}</td>

<td>Monitor</td>

</tr>

`;

        }

    );

}
