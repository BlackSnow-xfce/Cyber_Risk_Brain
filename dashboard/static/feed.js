function renderFeed(data) {

    const feed =
        document.querySelector(".feed");

    if (!feed)
        return;

    feed.innerHTML = "";

    data.findings

        .slice(0,5)

        .forEach(

            finding => {

                feed.innerHTML += `

<div class="feed-item">

<div class="feed-time">

LIVE

</div>

<div>

<strong>

${finding.title}

</strong>

<br>

${finding.risk_level}

•

${finding.score}

</div>

</div>

`;

            }

        );

}
