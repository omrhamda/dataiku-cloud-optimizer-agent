"""Embedded base strategy interface."""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class OptimizationStrategy(ABC):
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config: Dict[str, Any] = config or {}

    @abstractmethod
    def optimize(self, cost_data: Dict[str, Any]) -> Dict[str, Any]:  # pragma: no cover - interface
        pass

    @abstractmethod
    def calculate_confidence(self, data: Dict[str, Any]) -> float:  # pragma: no cover - interface
        pass

    def get_strategy_name(self) -> str:
        return self.__class__.__name__
