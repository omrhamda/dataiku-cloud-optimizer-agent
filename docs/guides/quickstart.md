# Quick Start Guide

This guide will help you get started with the Dataiku Cloud Optimizer Agent in just a few minutes.

## 1. Installation

First, install the agent:

```bash
pip install dataiku-cloud-optimizer
```

## 2. Initialize Configuration

Create a sample configuration file:

```bash
dataiku-optimizer config init --output config.yaml
```

This creates a template configuration file with all available options.

## 3. Configure Cloud Providers

Edit the generated `config.yaml` file to add your cloud provider credentials:

```yaml
providers:
  aws:
    region: us-east-1
    profile: default
  azure:
    subscription_id: your-subscription-id
  gcp:
    project_id: your-project-id
```

## 4. Configure Integrations (Optional)

If you're using Dataiku or Databricks, add their configurations:

```yaml
integrations:
  dataiku:
    url: https://your-dataiku-instance.com
    api_key: your-api-key
  databricks:
    workspace_url: https://your-workspace.cloud.databricks.com
    token: your-token
```

## 5. Analyze Cloud Costs

Start by analyzing costs for a specific provider:

```bash
# Analyze AWS costs
dataiku-optimizer analyze --provider aws

# Get detailed JSON output
dataiku-optimizer analyze --provider aws --output json
```

## 6. Get Optimization Recommendations

Get recommendations for all configured providers:

```bash
dataiku-optimizer recommendations
```

Or for a specific provider:

```bash
dataiku-optimizer recommendations --provider aws
```

## 7. Run Optimization Analysis

Run a complete optimization analysis:

```bash
dataiku-optimizer optimize --provider aws --strategy cost_optimization
```

## Example Workflow

Here's a complete example workflow:

```bash
# 1. Initialize configuration
dataiku-optimizer config init --output my-config.yaml

# 2. Edit configuration file (add your credentials)
# ... edit my-config.yaml ...

# 3. Use the configuration file
dataiku-optimizer --config my-config.yaml analyze --provider aws

# 4. Get recommendations with JSON output for automation
dataiku-optimizer --config my-config.yaml recommendations --output json > recommendations.json

# 5. Run optimization analysis
dataiku-optimizer --config my-config.yaml optimize --provider aws
```

## Understanding the Output

### Cost Analysis Output

```json
{
  "provider": "aws",
  "total_cost": 1250.75,
  "period": "2024-11-01 to 2024-12-01",
  "resource_count": 45,
  "services": {
    "EC2": 850.50,
    "RDS": 275.25,
    "S3": 125.00
  },
  "regions": {
    "us-east-1": 900.00,
    "us-west-2": 350.75
  }
}
```

### Recommendations Output

```
=== Cloud Optimization Recommendations ===
Total Potential Savings: $375.50

AWS:
  Savings: $187.75
  Confidence: 85.0%
  Top Recommendation: Rightsize overprovisioned instances to save ~15% of compute costs
```

## Next Steps

- **Learn about providers**: See the [Cloud Providers Guide](providers.md)
- **Explore strategies**: Read about [Optimization Strategies](strategies.md)
- **Set up integrations**: Configure [Dataiku and Databricks integrations](integrations.md)
- **Automate workflows**: Use the CLI in scripts and CI/CD pipelines
- **Advanced usage**: Check out [Advanced Examples](../examples/advanced.md)

## Common Use Cases

### Daily Cost Monitoring

Set up a daily cron job to monitor costs:

```bash
# Add to crontab
0 9 * * * /usr/local/bin/dataiku-optimizer recommendations --output json > /var/log/cost-recommendations.json
```

### CI/CD Integration

Include cost analysis in your deployment pipeline:

```yaml
# .github/workflows/cost-analysis.yml
- name: Analyze Cloud Costs
  run: |
    dataiku-optimizer analyze --provider aws --output json
    dataiku-optimizer recommendations --output json
```

### Automated Reporting

Generate weekly cost reports:

```bash
#!/bin/bash
DATE=$(date +%Y-%m-%d)
dataiku-optimizer analyze --provider aws --output json > "report-aws-$DATE.json"
dataiku-optimizer analyze --provider azure --output json > "report-azure-$DATE.json"
dataiku-optimizer recommendations --output json > "recommendations-$DATE.json"
```