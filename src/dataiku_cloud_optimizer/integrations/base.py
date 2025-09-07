"""
Base integration interface
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


class Integration(ABC):
    """Abstract base class for platform integrations"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._authenticated = False
        
    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticate with the platform"""
        pass
    
    @abstractmethod
    def get_workload_data(self) -> List[Dict[str, Any]]:
        """Get workload/job execution data"""
        pass
    
    @abstractmethod
    def get_resource_usage(self) -> Dict[str, Any]:
        """Get resource utilization data"""
        pass
    
    @abstractmethod
    def apply_recommendations(self, recommendations: List[Dict[str, Any]]) -> bool:
        """Apply optimization recommendations to the platform"""
        pass
    
    def is_authenticated(self) -> bool:
        """Check if integration is authenticated"""
        return self._authenticated