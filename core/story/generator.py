class StoryGenerator:

    def generate(self, asset, risk):

        story = (
            f"Asset '{asset}' erreicht einen Risikoscore von "
            f"{risk['score']}/100.\n\n"
        )

        if risk["reasons"]:

            story += "Gründe:\n"

            for reason in risk["reasons"]:

                story += f"- {reason}\n"

        return story
