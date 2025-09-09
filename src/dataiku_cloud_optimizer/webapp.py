"""
FastAPI web application exposing agent capabilities and a simple UI hook.
"""

from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from .core import CloudOptimizerAgent
from .providers import AWSProvider, AzureProvider, GCPProvider
from .strategies import CostOptimizationStrategy


class ProactiveRunRequest(BaseModel):
    provider: Optional[str] = None
    channels: Optional[List[str]] = None
    org_context: Optional[Dict[str, Any]] = None


def create_app(agent: Optional[CloudOptimizerAgent] = None) -> FastAPI:
    app = FastAPI(title="Dataiku Cloud Optimizer Agent")

    _agent = agent or CloudOptimizerAgent()
    # Register defaults if empty
    if not _agent.providers:
        _agent.register_provider("aws", AWSProvider())
        _agent.register_provider("azure", AzureProvider())
        _agent.register_provider("gcp", GCPProvider())
    if not _agent.strategies:
        _agent.register_strategy("cost_optimization", CostOptimizationStrategy())

    @app.get("/health")
    def health() -> Dict[str, str]:
        return {"status": "ok"}

    @app.get("/", response_class=HTMLResponse)
    def index() -> str:
        return (
            "<html><head><title>Cloud Optimizer Agent</title></head>"
            "<body>"
            "<h1>Dataiku Cloud Optimizer Agent</h1>"
            "<p>Use /recommendations to fetch insights or POST to /proactive/run to trigger notifications.</p>"
            "</body></html>"
        )

    @app.get("/recommendations")
    def get_recommendations(provider: Optional[str] = None) -> List[Dict[str, Any]]:
        results = _agent.get_recommendations(provider)
        return [
            {
                "provider": r.provider,
                "resource_type": r.resource_type,
                "current_cost": r.current_cost,
                "optimized_cost": r.optimized_cost,
                "savings": r.savings,
                "recommendations": r.recommendations,
                "confidence_score": r.confidence_score,
                "timestamp": r.timestamp.isoformat(),
            }
            for r in results
        ]

    @app.post("/proactive/run")
    def proactive_run(body: ProactiveRunRequest) -> Dict[str, Any]:
        outcome = _agent.run_proactive_cycle(
            provider=body.provider, channels=body.channels, org_context=body.org_context
        )
        return outcome

    return app
