"""
Unit tests for AWS provider
"""


from dataiku_cloud_optimizer.providers.aws import AWSProvider


class TestAWSProvider:
    """Test cases for AWSProvider"""

    def test_initialization_default_config(self):
        """Test AWS provider initialization with default config"""
        provider = AWSProvider()

        assert provider.region == "us-east-1"
        assert provider.profile == "default"
        assert not provider._authenticated

    def test_initialization_custom_config(self, sample_aws_config):
        """Test AWS provider initialization with custom config"""
        provider = AWSProvider(sample_aws_config)

        assert provider.region == "us-east-1"
        assert provider.profile == "test"
        assert not provider._authenticated

    def test_authenticate_success(self, sample_aws_config):
        """Test successful authentication"""
        provider = AWSProvider(sample_aws_config)

        result = provider.authenticate()

        assert result is True
        assert provider._authenticated is True

    def test_get_cost_data_default_dates(self, sample_aws_config):
        """Test getting cost data with default date range"""
        provider = AWSProvider(sample_aws_config)

        result = provider.get_cost_data()

        assert result["provider"] == "aws"
        assert "total_cost" in result
        assert "resource_count" in result
        assert "services" in result
        assert "regions" in result
        assert provider._authenticated is True

    def test_get_cost_data_custom_dates(self, sample_aws_config):
        """Test getting cost data with custom date range"""
        provider = AWSProvider(sample_aws_config)

        result = provider.get_cost_data(start_date="2024-11-01", end_date="2024-11-30")

        assert result["provider"] == "aws"
        assert "2024-11-01 to 2024-11-30" in result["period"]

    def test_get_resource_inventory(self, sample_aws_config):
        """Test getting resource inventory"""
        provider = AWSProvider(sample_aws_config)

        result = provider.get_resource_inventory()

        assert isinstance(result, list)
        assert len(result) > 0
        assert provider._authenticated is True

        # Check first resource structure
        resource = result[0]
        assert "resource_id" in resource
        assert "resource_type" in resource
        assert "instance_type" in resource
        assert "state" in resource

    def test_get_recommendations(self, sample_aws_config):
        """Test getting optimization recommendations"""
        provider = AWSProvider(sample_aws_config)

        result = provider.get_recommendations()

        assert isinstance(result, list)
        assert len(result) > 0
        assert provider._authenticated is True

        # Check recommendation structure
        rec = result[0]
        assert "type" in rec
        assert "estimated_savings" in rec
        assert "confidence" in rec
        assert "reason" in rec

    def test_get_rightsizing_opportunities(self, sample_aws_config):
        """Test getting rightsizing opportunities"""
        provider = AWSProvider(sample_aws_config)

        result = provider.get_rightsizing_opportunities()

        assert isinstance(result, list)
        assert len(result) > 0
        assert provider._authenticated is True

        # Check opportunity structure
        opp = result[0]
        assert "instance_id" in opp
        assert "current_type" in opp
        assert "recommended_type" in opp
        assert "monthly_savings" in opp
        assert "confidence_score" in opp

    def test_get_unused_resources(self, sample_aws_config):
        """Test getting unused resources"""
        provider = AWSProvider(sample_aws_config)

        result = provider.get_unused_resources()

        assert isinstance(result, list)
        assert len(result) > 0
        assert provider._authenticated is True

        # Check unused resource structure
        resource = result[0]
        assert "resource_id" in resource
        assert "resource_type" in resource
        assert "monthly_cost" in resource
        assert "recommendation" in resource

    def test_get_default_date_range(self, sample_aws_config):
        """Test getting default date range"""
        provider = AWSProvider(sample_aws_config)

        start_date, end_date = provider.get_default_date_range()

        assert isinstance(start_date, str)
        assert isinstance(end_date, str)
        assert len(start_date) == 10  # YYYY-MM-DD format
        assert len(end_date) == 10
        assert start_date < end_date

    def test_validate_date_range_valid(self, sample_aws_config):
        """Test date range validation with valid dates"""
        provider = AWSProvider(sample_aws_config)

        result = provider.validate_date_range("2024-01-01", "2024-01-31")

        assert result is True

    def test_validate_date_range_invalid_format(self, sample_aws_config):
        """Test date range validation with invalid format"""
        provider = AWSProvider(sample_aws_config)

        result = provider.validate_date_range("2024/01/01", "2024/01/31")

        assert result is False

    def test_validate_date_range_invalid_order(self, sample_aws_config):
        """Test date range validation with invalid order"""
        provider = AWSProvider(sample_aws_config)

        result = provider.validate_date_range("2024-01-31", "2024-01-01")

        assert result is False
