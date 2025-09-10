"""
Unit tests for the core CloudOptimizerAgent
"""

import pytest

from dataiku_cloud_optimizer.core import CloudOptimizerAgent, OptimizationResult
from dataiku_cloud_optimizer.providers.base import CloudProvider
from dataiku_cloud_optimizer.strategies.base import OptimizationStrategy


class MockProvider(CloudProvider):
    """Mock cloud provider for testing"""

    def authenticate(self):
        return True

    def get_cost_data(self, **kwargs):
        return {"provider": "mock", "total_cost": 500.0, "resource_count": 10}

    def get_resource_inventory(self):
        return []

    def get_recommendations(self):
        return []

    def get_rightsizing_opportunities(self):
        return []

    def get_unused_resources(self):
        return []


class MockStrategy(OptimizationStrategy):
    """Mock optimization strategy for testing"""

    def optimize(self, cost_data):
        return {
            "resource_type": "test",
            "current_cost": 500.0,
            "optimized_cost": 400.0,
            "savings": 100.0,
            "recommendations": ["Test recommendation"],
            "confidence_score": 0.8,
        }

    def calculate_confidence(self, data):
        return 0.8


class TestCloudOptimizerAgent:
    """Test cases for CloudOptimizerAgent"""

    def test_initialization(self):
        """Test agent initialization"""
        agent = CloudOptimizerAgent()
        assert len(agent.providers) == 0
        assert len(agent.strategies) == 0
        assert len(agent.integrations) == 0

    def test_register_provider(self):
        """Test provider registration"""
        agent = CloudOptimizerAgent()
        provider = MockProvider()

        agent.register_provider("test", provider)

        assert "test" in agent.providers
        assert agent.providers["test"] == provider

    def test_register_strategy(self):
        """Test strategy registration"""
        agent = CloudOptimizerAgent()
        strategy = MockStrategy()

        agent.register_strategy("test", strategy)

        assert "test" in agent.strategies
        assert agent.strategies["test"] == strategy

    def test_analyze_costs_success(self):
        """Test successful cost analysis"""
        agent = CloudOptimizerAgent()
        provider = MockProvider()
        agent.register_provider("test", provider)

        result = agent.analyze_costs("test")

        assert result["provider"] == "mock"
        assert result["total_cost"] == 500.0
        assert result["resource_count"] == 10

    def test_analyze_costs_unknown_provider(self):
        """Test cost analysis with unknown provider"""
        agent = CloudOptimizerAgent()

        with pytest.raises(ValueError, match="Provider unknown not registered"):
            agent.analyze_costs("unknown")

    def test_optimize_success(self):
        """Test successful optimization"""
        agent = CloudOptimizerAgent()
        provider = MockProvider()
        strategy = MockStrategy()

        agent.register_provider("test", provider)
        agent.register_strategy("test", strategy)

        result = agent.optimize("test", "test")

        assert isinstance(result, OptimizationResult)
        assert result.provider == "test"
        assert result.resource_type == "test"
        assert result.current_cost == 500.0
        assert result.optimized_cost == 400.0
        assert result.savings == 100.0
        assert len(result.recommendations) == 1
        assert result.confidence_score == 0.8

    def test_optimize_unknown_provider(self):
        """Test optimization with unknown provider"""
        agent = CloudOptimizerAgent()
        strategy = MockStrategy()
        agent.register_strategy("test", strategy)

        with pytest.raises(ValueError, match="Provider unknown not registered"):
            agent.optimize("unknown", "test")

    def test_optimize_unknown_strategy(self):
        """Test optimization with unknown strategy"""
        agent = CloudOptimizerAgent()
        provider = MockProvider()
        agent.register_provider("test", provider)

        with pytest.raises(ValueError, match="Strategy unknown not registered"):
            agent.optimize("test", "unknown")

    def test_get_recommendations_with_provider(self):
        """Test getting recommendations for specific provider"""
        agent = CloudOptimizerAgent()
        provider = MockProvider()
        strategy = MockStrategy()

        agent.register_provider("test", provider)
        agent.register_strategy("test", strategy)

        results = agent.get_recommendations("test")

        assert len(results) == 1
        assert isinstance(results[0], OptimizationResult)
        assert results[0].provider == "test"

    def test_get_recommendations_all_providers(self):
        """Test getting recommendations for all providers"""
        agent = CloudOptimizerAgent()
        provider1 = MockProvider()
        provider2 = MockProvider()
        strategy = MockStrategy()

        agent.register_provider("test1", provider1)
        agent.register_provider("test2", provider2)
        agent.register_strategy("test", strategy)

        results = agent.get_recommendations()

        assert len(results) == 2
        provider_names = [r.provider for r in results]
        assert "test1" in provider_names
        assert "test2" in provider_names

    def test_get_recommendations_no_strategies(self):
        """Test getting recommendations when no strategies are registered"""
        agent = CloudOptimizerAgent()
        provider = MockProvider()
        agent.register_provider("test", provider)

        results = agent.get_recommendations("test")

        assert len(results) == 0
