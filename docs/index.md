# Dataiku Cloud Optimizer Agent

A Dataiku-driven agent to optimize multi-cloud (AWS, Azure, GCP) and Databricks workloads. This tool ingests cloud costs, analyzes Databricks job history, and recommends right-sized clusters and policies.

## Features

- **Multi-cloud support**: Works with AWS, Azure, and Google Cloud Platform
- **Dataiku integration**: Native integration with Dataiku DSS for workload analysis
- **Databricks optimization**: Specialized support for Databricks cluster optimization
- **Intelligent recommendations**: AI-driven cost optimization suggestions
- **CLI interface**: Easy-to-use command-line interface for automation
- **Extensible architecture**: Plugin-based system for custom strategies and integrations

## Quick Start

### Installation

```bash
pip install dataiku-cloud-optimizer
```

### Basic Usage

1. **Initialize configuration**:
   ```bash
   dataiku-optimizer config init
   ```

2. **Analyze cloud costs**:
   ```bash
   dataiku-optimizer analyze --provider aws
   ```

3. **Get optimization recommendations**:
   ```bash
   dataiku-optimizer recommendations
   ```

## Architecture

The Dataiku Cloud Optimizer Agent follows a modular architecture:

- **Providers**: Cloud provider integrations (AWS, Azure, GCP)
- **Strategies**: Optimization strategies and algorithms
- **Integrations**: Platform integrations (Dataiku, Databricks)
- **CLI**: Command-line interface for user interaction

## Documentation

- [Installation Guide](guides/installation.md)
- [Quick Start Tutorial](guides/quickstart.md)
- [API Reference](api/core.md)
- [Examples](examples/basic.md)

## Contributing

We welcome contributions! Please see our [Contributing Guide](contributing.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.