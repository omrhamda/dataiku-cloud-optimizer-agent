"""
Base optimization strategy interface
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class OptimizationStrategy(ABC):
    """Abstract base class for optimization strategies"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

    @abstractmethod
    def optimize(self, cost_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply optimization strategy to cost data

        Args:
            cost_data: Cost and resource data from cloud provider

        Returns:
            Dictionary containing optimization results with keys:
            - resource_type: Type of resource being optimized
            - current_cost: Current cost
            - optimized_cost: Projected cost after optimization
            - savings: Projected savings
            - recommendations: List of specific recommendations
            - confidence_score: Confidence level of recommendations (0.0-1.0)
        """
        pass

    @abstractmethod
    def calculate_confidence(self, data: Dict[str, Any]) -> float:
        """Calculate confidence score for optimization recommendations"""
        pass

    def get_strategy_name(self) -> str:
        """Get the name of this strategy"""
        return self.__class__.__name__
