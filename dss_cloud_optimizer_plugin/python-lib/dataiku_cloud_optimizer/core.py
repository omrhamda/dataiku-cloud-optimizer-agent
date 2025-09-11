"""Embedded core agent (subset) for DSS plugin."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from .providers.base import CloudProvider
from .strategies.base import OptimizationStrategy

@dataclass
class OptimizationResult:
    provider: str
    resource_type: str
    current_cost: float
    optimized_cost: float
    savings: float
    recommendations: List[str]
    confidence_score: float
    timestamp: datetime

class CloudOptimizerAgent:
    def __init__(self) -> None:
        self.providers: Dict[str, CloudProvider] = {}
        self.strategies: Dict[str, OptimizationStrategy] = {}

    def register_provider(self, name: str, provider: CloudProvider) -> None:
        self.providers[name] = provider

    def register_strategy(self, name: str, strategy: OptimizationStrategy) -> None:
        self.strategies[name] = strategy

    def optimize(self, provider_name: str, strategy_name: str) -> OptimizationResult:
        if provider_name not in self.providers:
            raise ValueError(f"Provider {provider_name} not registered")
        if strategy_name not in self.strategies:
            raise ValueError(f"Strategy {strategy_name} not registered")
        provider = self.providers[provider_name]
        strategy = self.strategies[strategy_name]
        cost_data = provider.get_cost_data()
        opt = strategy.optimize(cost_data)
        return OptimizationResult(
            provider=provider_name,
            resource_type=opt.get("resource_type", "unknown"),
            current_cost=opt.get("current_cost", 0.0),
            optimized_cost=opt.get("optimized_cost", 0.0),
            savings=opt.get("savings", 0.0),
            recommendations=opt.get("recommendations", []),
            confidence_score=opt.get("confidence_score", 0.0),
            timestamp=datetime.now(),
        )

    def run_strategy(self, strategy_name: str) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for prov_name in self.providers.keys():
            try:
                res = self.optimize(prov_name, strategy_name)
                results.append({
                    "provider": res.provider,
                    "resource_type": res.resource_type,
                    "savings": res.savings,
                    "confidence_score": res.confidence_score,
                    "recommendations": res.recommendations,
                })
            except Exception as e:  # pragma: no cover
                print(f"Error optimizing {prov_name}: {e}")
        return results
