function renderGraph(data){

    const graph =
        document.getElementById(
            "graphSummary"
        );

    if(graph)

        graph.textContent=

            JSON.stringify(

                data.graph??{},

                null,

                2

            );

    const team =
        document.getElementById(
            "teamRisk"
        );

    if(team)

        team.textContent=

            JSON.stringify(

                data.team_risk??{},

                null,

                2

            );

}
