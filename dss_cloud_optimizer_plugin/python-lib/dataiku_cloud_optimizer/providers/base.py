"""Base provider abstraction (embedded)."""
from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

class CloudProvider(ABC):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    @abstractmethod
    def authenticate(self) -> bool:  # pragma: no cover - interface
        pass

    @abstractmethod
    def get_cost_data(self, start_date: Optional[str] = None, end_date: Optional[str] = None, **kwargs) -> Dict[str, Any]:  # pragma: no cover - interface
        pass

    @abstractmethod
    def get_resource_inventory(self) -> List[Dict[str, Any]]:  # pragma: no cover - interface
        pass

    @abstractmethod
    def get_recommendations(self) -> List[Dict[str, Any]]:  # pragma: no cover - interface
        pass

    @abstractmethod
    def get_rightsizing_opportunities(self) -> List[Dict[str, Any]]:  # pragma: no cover - interface
        pass

    @abstractmethod
    def get_unused_resources(self) -> List[Dict[str, Any]]:  # pragma: no cover - interface
        pass

    def get_default_date_range(self) -> Tuple[str, str]:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")

    def validate_date_range(self, start_date: str, end_date: str) -> bool:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            return start <= end
        except ValueError:
            return False
