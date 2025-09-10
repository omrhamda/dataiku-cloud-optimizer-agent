"""Integration tests for the full optimizer workflow."""

import tempfile
from pathlib import Path

import pytest

from dataiku_cloud_optimizer.core import CloudOptimizerAgent
from dataiku_cloud_optimizer.integrations import (
    DatabricksIntegration,
    DataikuIntegration,
)
from dataiku_cloud_optimizer.providers import AWSProvider, AzureProvider, GCPProvider
from dataiku_cloud_optimizer.strategies import CostOptimizationStrategy
from dataiku_cloud_optimizer.utils.config import get_default_config, load_config


class TestFullWorkflow:
    """Integration tests for complete workflows"""

    def test_complete_optimization_workflow(self):
        """Test complete optimization workflow from start to finish"""
        # Initialize agent
        agent = CloudOptimizerAgent()

        # Register providers
        agent.register_provider("aws", AWSProvider())
        agent.register_provider("azure", AzureProvider())
        agent.register_provider("gcp", GCPProvider())

        # Register strategy
        agent.register_strategy("cost_optimization", CostOptimizationStrategy())

        # Test cost analysis for each provider
        aws_costs = agent.analyze_costs("aws")
        assert aws_costs["provider"] == "aws"
        assert aws_costs["total_cost"] > 0

        azure_costs = agent.analyze_costs("azure")
        assert azure_costs["provider"] == "azure"
        assert azure_costs["total_cost"] > 0

        gcp_costs = agent.analyze_costs("gcp")
        assert gcp_costs["provider"] == "gcp"
        assert gcp_costs["total_cost"] > 0

        # Test optimization for each provider
        aws_optimization = agent.optimize("aws", "cost_optimization")
        assert aws_optimization.provider == "aws"
        assert aws_optimization.savings >= 0

        azure_optimization = agent.optimize("azure", "cost_optimization")
        assert azure_optimization.provider == "azure"
        assert azure_optimization.savings >= 0

        gcp_optimization = agent.optimize("gcp", "cost_optimization")
        assert gcp_optimization.provider == "gcp"
        assert gcp_optimization.savings >= 0

        # Test getting recommendations for all providers
        recommendations = agent.get_recommendations()
        assert len(recommendations) == 3

        provider_names = [r.provider for r in recommendations]
        assert "aws" in provider_names
        assert "azure" in provider_names
        assert "gcp" in provider_names

    def test_configuration_workflow(self):
        """Test configuration loading and validation workflow"""
        # Create a temporary config file
        config_data = get_default_config()
        config_data["providers"]["aws"]["region"] = "us-west-2"
        config_data["integrations"]["dataiku"]["url"] = "https://test.com"
        config_data["integrations"]["dataiku"]["api_key"] = "test-key"
        config_data["integrations"]["databricks"]["workspace_url"] = (
            "https://test.databricks.com"
        )
        config_data["integrations"]["databricks"]["token"] = "test-token"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            import yaml

            yaml.dump(config_data, f)
            config_path = f.name

        try:
            # Load and validate configuration
            loaded_config = load_config(config_path)
            assert loaded_config["providers"]["aws"]["region"] == "us-west-2"

            # Test config merging
            override_config = {"providers": {"aws": {"profile": "test"}}}

            from dataiku_cloud_optimizer.utils.config import merge_configs

            merged_config = merge_configs(loaded_config, override_config)
            assert merged_config["providers"]["aws"]["region"] == "us-west-2"
            assert merged_config["providers"]["aws"]["profile"] == "test"

        finally:
            Path(config_path).unlink()

    def test_integration_workflow(self):
        """Test integration workflow with Dataiku and Databricks"""
        # Initialize integrations
        dataiku_config = {
            "url": "https://test-dataiku.com",
            "api_key": "test-key",
            "project_key": "TEST",
        }
        dataiku_integration = DataikuIntegration(dataiku_config)

        databricks_config = {
            "workspace_url": "https://test-databricks.com",
            "token": "test-token",
        }
        databricks_integration = DatabricksIntegration(databricks_config)

        # Test authentication
        assert dataiku_integration.authenticate()
        assert databricks_integration.authenticate()

        # Test workload data retrieval
        dataiku_workloads = dataiku_integration.get_workload_data()
        assert len(dataiku_workloads) > 0
        assert "job_id" in dataiku_workloads[0]

        databricks_workloads = databricks_integration.get_workload_data()
        assert len(databricks_workloads) > 0
        assert "job_id" in databricks_workloads[0]

        # Test resource usage data
        dataiku_usage = dataiku_integration.get_resource_usage()
        assert "clusters" in dataiku_usage
        assert "summary" in dataiku_usage

        databricks_usage = databricks_integration.get_resource_usage()
        assert "clusters" in databricks_usage
        assert "summary" in databricks_usage

        # Test applying recommendations
        test_recommendations = [
            {
                "type": "rightsizing",
                "cluster_id": "test-cluster",
                "current_node_type": "large",
                "recommended_node_type": "medium",
            }
        ]

        assert dataiku_integration.apply_recommendations(test_recommendations)
        assert databricks_integration.apply_recommendations(test_recommendations)

    def test_provider_strategy_combinations(self):
        """Test all provider and strategy combinations"""
        agent = CloudOptimizerAgent()

        # Register all providers
        providers = {
            "aws": AWSProvider(),
            "azure": AzureProvider(),
            "gcp": GCPProvider(),
        }

        for name, provider in providers.items():
            agent.register_provider(name, provider)

        # Register strategy
        strategy = CostOptimizationStrategy()
        agent.register_strategy("cost_optimization", strategy)

        # Test all combinations
        for provider_name in providers.keys():
            # Test cost analysis
            costs = agent.analyze_costs(provider_name)
            assert costs["provider"] == provider_name
            assert "total_cost" in costs

            # Test optimization
            result = agent.optimize(provider_name, "cost_optimization")
            assert result.provider == provider_name
            assert result.current_cost >= 0
            assert result.optimized_cost >= 0
            assert result.savings >= 0
            assert 0 <= result.confidence_score <= 1
            assert len(result.recommendations) >= 0

    def test_error_handling_workflow(self):
        """Test error handling in various scenarios"""
        agent = CloudOptimizerAgent()

        # Test unknown provider
        with pytest.raises(ValueError, match="Provider unknown not registered"):
            agent.analyze_costs("unknown")

        # Test unknown strategy
        aws_provider = AWSProvider()
        agent.register_provider("aws", aws_provider)

        with pytest.raises(ValueError, match="Strategy unknown not registered"):
            agent.optimize("aws", "unknown")

        # Test missing integrations
        agent.register_integration("test", None)
        # Should not raise error, just handle gracefully
        _ = agent.get_recommendations()
        # Should work with available providers and strategies

    def test_real_world_scenario(self):
        """Test a realistic end-to-end scenario"""
        # Simulate a real-world scenario with multiple providers and integrations
        agent = CloudOptimizerAgent()

        # Set up providers with custom configurations
        aws_config = {"region": "us-east-1", "profile": "production"}
        azure_config = {"subscription_id": "prod-sub-123"}

        agent.register_provider("aws", AWSProvider(aws_config))
        agent.register_provider("azure", AzureProvider(azure_config))

        # Set up strategy with custom thresholds
        strategy_config = {
            "min_savings_threshold": 50.0,  # Higher threshold
            "confidence_threshold": 0.8,
        }
        agent.register_strategy(
            "cost_optimization", CostOptimizationStrategy(strategy_config)
        )

        # Set up integrations
        dataiku_config = {
            "url": "https://prod-dataiku.company.com",
            "api_key": "prod-key",
            "project_key": "PRODUCTION",
        }
        agent.register_integration("dataiku", DataikuIntegration(dataiku_config))

        # Perform analysis workflow
        results = {}

        # 1. Analyze costs for each provider
        for provider in ["aws", "azure"]:
            results[f"{provider}_costs"] = agent.analyze_costs(provider)

        # 2. Get optimization recommendations
        recommendations = agent.get_recommendations()
        results["recommendations"] = recommendations

        # 3. Verify results
        assert len(results["recommendations"]) == 2  # AWS and Azure

        total_savings = sum(r.savings for r in recommendations)
        assert total_savings >= 0

        # 4. Get integration data
        dataiku_integration = agent.integrations["dataiku"]
        workload_data = dataiku_integration.get_workload_data()
        results["workload_data"] = workload_data

        # Verify integration data
        assert len(workload_data) > 0
        assert "job_id" in workload_data[0]
        assert "cost" in workload_data[0]

        # All results should be valid
        for _key, value in results.items():
            assert value is not None
            if isinstance(value, list):
                assert len(value) >= 0
