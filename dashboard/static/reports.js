function renderReports(data){

    const reports =
        document.getElementById(
            "reports"
        );

    if(reports)

        reports.textContent=

            JSON.stringify(

                data.reports??{},

                null,

                2

            );

}
