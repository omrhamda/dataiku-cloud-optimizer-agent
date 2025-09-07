# Installation

## Requirements

- Python 3.8 or higher
- pip (Python package installer)

## Install from PyPI

```bash
pip install dataiku-cloud-optimizer
```

## Install with Development Dependencies

If you plan to contribute or need development tools:

```bash
pip install dataiku-cloud-optimizer[dev]
```

## Install with Documentation Dependencies

To build documentation locally:

```bash
pip install dataiku-cloud-optimizer[docs]
```

## Install from Source

For the latest development version:

```bash
git clone https://github.com/omrhamda/dataiku-cloud-optimizer-agent.git
cd dataiku-cloud-optimizer-agent
pip install -e .
```

## Verify Installation

Test that the installation was successful:

```bash
dataiku-optimizer --version
dataiku-optimizer --help
```

## Cloud Provider Setup

### AWS

1. Install AWS CLI and configure credentials:
   ```bash
   aws configure
   ```

2. Or set environment variables:
   ```bash
   export AWS_ACCESS_KEY_ID=your-access-key
   export AWS_SECRET_ACCESS_KEY=your-secret-key
   export AWS_DEFAULT_REGION=us-east-1
   ```

### Azure

1. Install Azure CLI and login:
   ```bash
   az login
   ```

2. Or use service principal:
   ```bash
   export AZURE_CLIENT_ID=your-client-id
   export AZURE_CLIENT_SECRET=your-client-secret
   export AZURE_TENANT_ID=your-tenant-id
   ```

### Google Cloud

1. Install gcloud CLI and authenticate:
   ```bash
   gcloud auth application-default login
   ```

2. Or set credentials file:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
   ```

## Integration Setup

### Dataiku

1. Generate API key in Dataiku DSS
2. Note your instance URL
3. Configure in the agent (see [Configuration Guide](configuration.md))

### Databricks

1. Generate personal access token in Databricks
2. Note your workspace URL
3. Configure in the agent (see [Configuration Guide](configuration.md))

## Troubleshooting

### Permission Issues

If you encounter permission errors, try installing in user mode:

```bash
pip install --user dataiku-cloud-optimizer
```

### Dependency Conflicts

Use a virtual environment to avoid conflicts:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install dataiku-cloud-optimizer
```

### Version Compatibility

Check Python version compatibility:

```bash
python --version  # Should be 3.8 or higher
```