"""
Unit tests for cost optimization strategy
"""

from dataiku_cloud_optimizer.strategies.cost_optimization import (
    CostOptimizationStrategy,
)


class TestCostOptimizationStrategy:
    """Test cases for CostOptimizationStrategy"""

    def test_initialization_default_config(self):
        """Test strategy initialization with default config"""
        strategy = CostOptimizationStrategy()

        assert strategy.min_savings_threshold == 10.0
        assert strategy.confidence_threshold == 0.7

    def test_initialization_custom_config(self):
        """Test strategy initialization with custom config"""
        config = {"min_savings_threshold": 25.0, "confidence_threshold": 0.8}
        strategy = CostOptimizationStrategy(config)

        assert strategy.min_savings_threshold == 25.0
        assert strategy.confidence_threshold == 0.8

    def test_optimize_with_high_cost(self, sample_cost_data):
        """Test optimization with high cost data"""
        strategy = CostOptimizationStrategy()

        result = strategy.optimize(sample_cost_data)

        assert result["resource_type"] == "multi-service"
        assert result["current_cost"] == 1000.0
        assert result["optimized_cost"] < result["current_cost"]
        assert result["savings"] > 0
        assert len(result["recommendations"]) > 0
        assert 0 <= result["confidence_score"] <= 1

    def test_optimize_with_low_cost(self):
        """Test optimization with low cost data"""
        low_cost_data = {"provider": "aws", "total_cost": 100.0, "resource_count": 5}
        strategy = CostOptimizationStrategy()

        result = strategy.optimize(low_cost_data)

        assert result["current_cost"] == 100.0
        assert result["savings"] >= 0
        # Should have fewer recommendations for low cost
        assert len(result["recommendations"]) < 4

    def test_calculate_confidence_complete_data(self, sample_cost_data):
        """Test confidence calculation with complete data"""
        strategy = CostOptimizationStrategy()

        confidence = strategy.calculate_confidence(sample_cost_data)

        assert 0 <= confidence <= 1
        assert confidence > 0.5  # Should be high for complete data

    def test_calculate_confidence_minimal_data(self):
        """Test confidence calculation with minimal data"""
        minimal_data = {"total_cost": 500.0}
        strategy = CostOptimizationStrategy()

        confidence = strategy.calculate_confidence(minimal_data)

        assert 0 <= confidence <= 1
        assert confidence < 0.8  # Should be lower for incomplete data

    def test_get_strategy_name(self):
        """Test getting strategy name"""
        strategy = CostOptimizationStrategy()

        name = strategy.get_strategy_name()

        assert name == "CostOptimizationStrategy"

    def test_aws_specific_recommendations(self):
        """Test AWS-specific recommendations"""
        aws_data = {"provider": "aws", "total_cost": 1000.0, "resource_count": 20}
        strategy = CostOptimizationStrategy()

        result = strategy.optimize(aws_data)

        # Should include spot instance recommendation for AWS
        recommendations = result["recommendations"]
        spot_rec = any("Spot Instances" in rec for rec in recommendations)
        assert spot_rec

    def test_azure_specific_recommendations(self):
        """Test Azure-specific recommendations"""
        azure_data = {"provider": "azure", "total_cost": 1000.0, "resource_count": 20}
        strategy = CostOptimizationStrategy()

        result = strategy.optimize(azure_data)

        # Should include hybrid benefit recommendation for Azure
        recommendations = result["recommendations"]
        hybrid_rec = any("Hybrid Benefit" in rec for rec in recommendations)
        assert hybrid_rec

    def test_gcp_specific_recommendations(self):
        """Test GCP-specific recommendations"""
        gcp_data = {"provider": "gcp", "total_cost": 1000.0, "resource_count": 20}
        strategy = CostOptimizationStrategy()

        result = strategy.optimize(gcp_data)

        # Should include preemptible instance recommendation for GCP
        recommendations = result["recommendations"]
        preemptible_rec = any("Preemptible" in rec for rec in recommendations)
        assert preemptible_rec

    def test_recommendations_filtering(self):
        """Test filtering of recommendations by minimum savings"""
        config = {"min_savings_threshold": 100.0}  # High threshold
        strategy = CostOptimizationStrategy(config)

        low_cost_data = {
            "provider": "aws",
            "total_cost": 200.0,  # Low cost to generate small savings
            "resource_count": 5,
        }

        result = strategy.optimize(low_cost_data)

        # Should have fewer recommendations due to high threshold
        detailed_recs = result.get("detailed_recommendations", [])
        for rec in detailed_recs:
            assert rec["savings"] >= 100.0
