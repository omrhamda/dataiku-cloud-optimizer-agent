"""
Core module for the Dataiku Cloud Optimizer Agent
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from .providers.base import CloudProvider
from .strategies.base import OptimizationStrategy
from .integrations.base import Integration


@dataclass
class OptimizationResult:
    """Result of an optimization analysis"""
    provider: str
    resource_type: str
    current_cost: float
    optimized_cost: float
    savings: float
    recommendations: List[str]
    confidence_score: float
    timestamp: datetime


class CloudOptimizerAgent:
    """
    Main agent class that orchestrates cloud optimization across multiple providers
    """
    
    def __init__(self):
        self.providers: Dict[str, CloudProvider] = {}
        self.strategies: Dict[str, OptimizationStrategy] = {}
        self.integrations: Dict[str, Integration] = {}
        
    def register_provider(self, name: str, provider: CloudProvider) -> None:
        """Register a cloud provider"""
        self.providers[name] = provider
        
    def register_strategy(self, name: str, strategy: OptimizationStrategy) -> None:
        """Register an optimization strategy"""
        self.strategies[name] = strategy
        
    def register_integration(self, name: str, integration: Integration) -> None:
        """Register an integration"""
        self.integrations[name] = integration
        
    def analyze_costs(self, provider_name: str, **kwargs) -> Dict[str, Any]:
        """Analyze costs for a specific provider"""
        if provider_name not in self.providers:
            raise ValueError(f"Provider {provider_name} not registered")
            
        provider = self.providers[provider_name]
        return provider.get_cost_data(**kwargs)
        
    def optimize(self, provider_name: str, strategy_name: str, **kwargs) -> OptimizationResult:
        """Run optimization for a specific provider using a strategy"""
        if provider_name not in self.providers:
            raise ValueError(f"Provider {provider_name} not registered")
        if strategy_name not in self.strategies:
            raise ValueError(f"Strategy {strategy_name} not registered")
            
        provider = self.providers[provider_name]
        strategy = self.strategies[strategy_name]
        
        # Get current cost data
        cost_data = provider.get_cost_data(**kwargs)
        
        # Apply optimization strategy
        optimization = strategy.optimize(cost_data)
        
        return OptimizationResult(
            provider=provider_name,
            resource_type=optimization.get("resource_type", "unknown"),
            current_cost=optimization.get("current_cost", 0.0),
            optimized_cost=optimization.get("optimized_cost", 0.0),
            savings=optimization.get("savings", 0.0),
            recommendations=optimization.get("recommendations", []),
            confidence_score=optimization.get("confidence_score", 0.0),
            timestamp=datetime.now()
        )
        
    def get_recommendations(self, provider_name: Optional[str] = None) -> List[OptimizationResult]:
        """Get optimization recommendations for one or all providers"""
        results = []
        
        providers_to_check = [provider_name] if provider_name else list(self.providers.keys())
        
        for prov_name in providers_to_check:
            if prov_name in self.providers:
                # Use the first available strategy for basic recommendations
                if self.strategies:
                    strategy_name = list(self.strategies.keys())[0]
                    try:
                        result = self.optimize(prov_name, strategy_name)
                        results.append(result)
                    except Exception as e:
                        # Log error but continue with other providers
                        print(f"Error optimizing {prov_name}: {e}")
                        
        return results