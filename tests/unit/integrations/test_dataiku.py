"""
Unit tests for Dataiku integration
"""

from dataiku_cloud_optimizer.integrations.dataiku import DataikuIntegration


class TestDataikuIntegration:
    """Test cases for DataikuIntegration"""

    def test_initialization_default_config(self):
        """Test integration initialization with default config"""
        integration = DataikuIntegration()

        assert integration.url == ""
        assert integration.api_key == ""
        assert integration.project_key == ""
        assert not integration._authenticated

    def test_initialization_custom_config(self, sample_dataiku_config):
        """Test integration initialization with custom config"""
        integration = DataikuIntegration(sample_dataiku_config)

        assert integration.url == "https://test-dataiku.com"
        assert integration.api_key == "test-api-key"
        assert integration.project_key == "TEST_PROJECT"

    def test_authenticate_success(self, sample_dataiku_config):
        """Test successful authentication"""
        integration = DataikuIntegration(sample_dataiku_config)

        result = integration.authenticate()

        assert result is True
        assert integration._authenticated is True

    def test_authenticate_missing_credentials(self):
        """Test authentication with missing credentials"""
        integration = DataikuIntegration()

        result = integration.authenticate()

        assert result is False
        assert integration._authenticated is False

    def test_get_workload_data(self, sample_dataiku_config):
        """Test getting workload data"""
        integration = DataikuIntegration(sample_dataiku_config)

        result = integration.get_workload_data()

        assert isinstance(result, list)
        assert len(result) > 0
        assert integration._authenticated is True

        # Check job structure
        job = result[0]
        assert "job_id" in job
        assert "project_key" in job
        assert "scenario" in job
        assert "resource_usage" in job
        assert "cost" in job

    def test_get_resource_usage(self, sample_dataiku_config):
        """Test getting resource usage data"""
        integration = DataikuIntegration(sample_dataiku_config)

        result = integration.get_resource_usage()

        assert "clusters" in result
        assert "summary" in result
        assert integration._authenticated is True

        # Check cluster structure
        cluster = result["clusters"][0]
        assert "cluster_id" in cluster
        assert "avg_cpu_utilization" in cluster
        assert "total_cost" in cluster

    def test_apply_recommendations(self, sample_dataiku_config):
        """Test applying recommendations"""
        integration = DataikuIntegration(sample_dataiku_config)

        recommendations = [
            {
                "type": "rightsizing",
                "cluster_id": "test-cluster",
                "current_node_type": "m5.large",
                "recommended_node_type": "m5.medium",
            },
            {
                "type": "auto_scaling",
                "cluster_id": "test-cluster",
                "recommended_min_nodes": 2,
                "recommended_max_nodes": 6,
            },
        ]

        result = integration.apply_recommendations(recommendations)

        assert result is True
        assert integration._authenticated is True

    def test_get_project_info(self, sample_dataiku_config):
        """Test getting project information"""
        integration = DataikuIntegration(sample_dataiku_config)

        result = integration.get_project_info()

        assert "projects" in result
        assert isinstance(result["projects"], list)
        assert len(result["projects"]) > 0

        # Check project structure
        project = result["projects"][0]
        assert "project_key" in project
        assert "name" in project
        assert "monthly_cost" in project
        assert "compute_clusters" in project

    def test_get_scenarios(self, sample_dataiku_config):
        """Test getting scenarios"""
        integration = DataikuIntegration(sample_dataiku_config)

        result = integration.get_scenarios()

        assert isinstance(result, list)
        assert len(result) > 0

        # Check scenario structure
        scenario = result[0]
        assert "scenario_id" in scenario
        assert "project_key" in scenario
        assert "schedule" in scenario
        assert "resource_requirements" in scenario

    def test_is_authenticated(self, sample_dataiku_config):
        """Test authentication status check"""
        integration = DataikuIntegration(sample_dataiku_config)

        assert not integration.is_authenticated()

        integration.authenticate()

        assert integration.is_authenticated()
