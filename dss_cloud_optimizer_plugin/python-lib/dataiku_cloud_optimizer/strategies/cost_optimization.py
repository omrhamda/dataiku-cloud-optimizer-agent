"""Embedded cost optimization strategy."""
from __future__ import annotations
import logging
from typing import Any, Dict, List, Optional
from .base import OptimizationStrategy

logger = logging.getLogger(__name__)

class CostOptimizationStrategy(OptimizationStrategy):
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(config)
        self.min_savings_threshold = self.config.get("min_savings_threshold", 10.0)

    def optimize(self, cost_data: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Optimizing cost data for provider={cost_data.get('provider','unknown')}")
        total_cost = cost_data.get("total_cost", 0.0)
        recs = self._generate_recommendations(cost_data)
        total_savings = sum(r.get("savings", 0) for r in recs)
        optimized_cost = max(0, total_cost - total_savings)
        confidence = self.calculate_confidence(cost_data)
        return {
            "resource_type": "multi-service",
            "current_cost": total_cost,
            "optimized_cost": optimized_cost,
            "savings": total_savings,
            "recommendations": [r["description"] for r in recs],
            "confidence_score": confidence,
            "detailed_recommendations": recs,
        }

    def _generate_recommendations(self, cost_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        recs: List[Dict[str, Any]] = []
        total_cost = cost_data.get("total_cost", 0.0)
        if total_cost > 500:
            recs.append({
                "type": "rightsizing",
                "description": "Rightsize overprovisioned instances",
                "savings": total_cost * 0.15,
                "confidence": 0.8,
            })
        if total_cost > 200:
            recs.append({
                "type": "unused_resources",
                "description": "Remove unused storage volumes and snapshots",
                "savings": min(total_cost * 0.08, 150),
                "confidence": 0.9,
            })
        return [r for r in recs if r["savings"] >= self.min_savings_threshold]

    def calculate_confidence(self, data: Dict[str, Any]) -> float:
        factors = []
        if data.get("total_cost", 0) > 0:
            factors.append(0.4)
        if data.get("resource_count", 0) > 0:
            factors.append(0.3)
        if data.get("services"):
            factors.append(0.3)
        return min(sum(factors), 1.0)
