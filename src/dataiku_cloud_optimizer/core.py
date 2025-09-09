"""
Core module for the Dataiku Cloud Optimizer Agent
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from .integrations.base import Integration
from .providers.base import CloudProvider
from .strategies.base import OptimizationStrategy


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
        # Optional components wired at runtime
        self.llm: Any = None
        self.notifiers: Dict[str, Any] = {}

    def register_provider(self, name: str, provider: CloudProvider) -> None:
        """Register a cloud provider"""
        self.providers[name] = provider

    def register_strategy(self, name: str, strategy: OptimizationStrategy) -> None:
        """Register an optimization strategy"""
        self.strategies[name] = strategy

    def register_integration(self, name: str, integration: Integration) -> None:
        """Register an integration"""
        self.integrations[name] = integration

    def register_llm(self, llm: Any) -> None:
        """Attach an LLM engine implementing .summarize(text, context) -> str"""
        self.llm = llm

    def register_notifier(self, name: str, notifier: Any) -> None:
        """Register a notifier implementing .send(message: str, **kwargs)"""
        self.notifiers[name] = notifier

    def analyze_costs(self, provider_name: str, **kwargs) -> Dict[str, Any]:
        """Analyze costs for a specific provider"""
        if provider_name not in self.providers:
            raise ValueError(f"Provider {provider_name} not registered")

        provider = self.providers[provider_name]
        return provider.get_cost_data(**kwargs)

    def optimize(
        self, provider_name: str, strategy_name: str, **kwargs
    ) -> OptimizationResult:
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
            timestamp=datetime.now(),
        )

    def get_recommendations(
        self, provider_name: Optional[str] = None
    ) -> List[OptimizationResult]:
        """Get optimization recommendations for one or all providers"""
        results = []

        providers_to_check = (
            [provider_name] if provider_name else list(self.providers.keys())
        )

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

    # --- Proactive agent capabilities ---
    def summarize_results(self, results: List[OptimizationResult], org_context: Optional[Dict[str, Any]] = None) -> str:
        """Use LLM (if available) to summarize optimization results for humans"""
        if not results:
            return "No optimization opportunities were found."

        # Fallback summary without LLM
        base_summary = []
        total_savings = sum(r.savings for r in results)
        base_summary.append(
            f"Found {len(results)} opportunities across providers with total potential savings ${total_savings:,.2f}."
        )
        for r in results[:5]:
            base_summary.append(
                f"- {r.provider.upper()}: save ${r.savings:,.2f} on {r.resource_type}; confidence {r.confidence_score:.0%}."
            )
        summary_text = "\n".join(base_summary)

        if self.llm is None:
            return summary_text

        try:
            # Prepare simple context payload
            ctx = {
                "org": (org_context or {}).get("name", ""),
                "date": datetime.now().isoformat(),
                "results": [
                    {
                        "provider": r.provider,
                        "resource_type": r.resource_type,
                        "savings": r.savings,
                        "recommendations": r.recommendations[:3],
                        "confidence": r.confidence_score,
                    }
                    for r in results
                ],
            }
            return self.llm.summarize(summary_text, ctx)
        except Exception as e:
            # Fallback to base summary on failure
            print(f"LLM summarization failed: {e}")
            return summary_text

    def notify(self, message: str, channels: Optional[List[str]] = None, **kwargs) -> Dict[str, bool]:
        """Send a notification message to one or more registered channels"""
        results: Dict[str, bool] = {}
        targets = channels or list(self.notifiers.keys())
        for name in targets:
            notifier = self.notifiers.get(name)
            if notifier is None:
                results[name] = False
                continue
            try:
                notifier.send(message, **kwargs)
                results[name] = True
            except Exception as e:
                print(f"Notifier '{name}' failed: {e}")
                results[name] = False
        return results

    def run_proactive_cycle(self, provider: Optional[str] = None, channels: Optional[List[str]] = None, org_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """End-to-end cycle: collect -> optimize -> summarize -> notify"""
        results = self.get_recommendations(provider)
        summary = self.summarize_results(results, org_context)
        notify_status = self.notify(summary, channels)
        return {"summary": summary, "notify": notify_status, "count": len(results)}
