from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.predator_engine import PredatorEngine

app = FastAPI(
    title="Cyber Risk Brain",
    version="2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


engine = PredatorEngine()


@app.get("/")
def root():
    return {
        "status": "Cyber Risk Brain Online",
        "engine": "PredatorAI v2",
    }


@app.get("/api/analyze")
def analyze():

    return engine.run()


@app.get("/api/findings")
def findings():

    return engine.run().get(
        "universal_findings",
        [],
    )


@app.get("/api/decisions")
def decisions():

    return engine.run().get(
        "decisions",
        [],
    )


@app.get("/api/reasoning")
def reasoning():

    return engine.run().get(
        "reasoning_results",
        [],
    )


@app.get("/api/story-bundles")
def story_bundles():

    return engine.run().get(
        "story_bundles",
        [],
    )


@app.get("/api/reports")
def reports():

    return engine.run().get(
        "reports",
        [],
    )


@app.get("/api/graph-summary")
def graph_summary():

    return engine.run().get(
        "graph_summary",
        {},
    )


@app.get("/api/team-risk")
def team_risk():

    return engine.run().get(
        "team_risk",
        {},
    )
