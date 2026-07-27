function renderStories(data){

    const stories =
        document.getElementById(
            "storyBundles"
        );

    if(stories)

        stories.textContent=

            JSON.stringify(

                data.story_bundles??{},

                null,

                2

            );

}
