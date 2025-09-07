"""
Base cloud provider interface
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta


class CloudProvider(ABC):
    """Abstract base class for cloud providers"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticate with the cloud provider"""
        pass
    
    @abstractmethod
    def get_cost_data(self, start_date: Optional[str] = None, end_date: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Get cost data for the specified time period"""
        pass
    
    @abstractmethod
    def get_resource_inventory(self) -> List[Dict[str, Any]]:
        """Get inventory of cloud resources"""
        pass
    
    @abstractmethod
    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Get provider-specific optimization recommendations"""
        pass
    
    @abstractmethod
    def get_rightsizing_opportunities(self) -> List[Dict[str, Any]]:
        """Get rightsizing opportunities for compute resources"""
        pass
    
    @abstractmethod
    def get_unused_resources(self) -> List[Dict[str, Any]]:
        """Get list of unused or underutilized resources"""
        pass
    
    def get_default_date_range(self) -> tuple[str, str]:
        """Get default date range for cost analysis (last 30 days)"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
    
    def validate_date_range(self, start_date: str, end_date: str) -> bool:
        """Validate date range format and logic"""
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            return start <= end
        except ValueError:
            return False