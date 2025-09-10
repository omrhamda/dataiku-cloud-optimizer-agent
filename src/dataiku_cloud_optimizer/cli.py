"""
Command Line Interface for Dataiku Cloud Optimizer Agent
"""

import json
import os
from pathlib import Path

import click
import uvicorn

from .core import CloudOptimizerAgent
from .integrations import DatabricksIntegration, DataikuIntegration
from .providers import AWSProvider, AzureProvider, GCPProvider
from .scheduler import AgentScheduler
from .strategies import CostOptimizationStrategy
from .utils.config import load_config
from .utils.llm import LLMEngine
from .utils.notify import EmailNotifier, SlackNotifier
from .webapp import create_app


@click.group()
@click.version_option(version="0.1.0")
@click.option(
    "--config",
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration file",
)
@click.pass_context
def cli(ctx, config):
    """Dataiku Cloud Optimizer Agent CLI"""
    ctx.ensure_object(dict)

    # Initialize the agent
    agent = CloudOptimizerAgent()

    # Load configuration if provided
    if config:
        config_data = load_config(config)
        ctx.obj["config"] = config_data
    else:
        ctx.obj["config"] = {}

    # Register providers (use config if available)
    providers_cfg = ctx.obj["config"].get("providers", {})
    agent.register_provider("aws", AWSProvider(providers_cfg.get("aws")))
    agent.register_provider("azure", AzureProvider(providers_cfg.get("azure")))
    agent.register_provider("gcp", GCPProvider(providers_cfg.get("gcp")))

    # Register default strategy
    agent.register_strategy("cost_optimization", CostOptimizationStrategy())

    # Register integrations (pass config)
    integrations_cfg = ctx.obj["config"].get("integrations", {})
    agent.register_integration(
        "dataiku", DataikuIntegration(integrations_cfg.get("dataiku"))
    )
    agent.register_integration(
        "databricks", DatabricksIntegration(integrations_cfg.get("databricks"))
    )

    # Wire optional LLM and notifiers
    llm_cfg = ctx.obj["config"].get("llm", {})
    if llm_cfg.get("provider") == "openai":
        api_key = llm_cfg.get("api_key") or os.getenv("OPENAI_API_KEY")
        model = llm_cfg.get("model", "gpt-4o-mini")
        if api_key:
            agent.register_llm(LLMEngine(api_key=api_key, model=model))

    notify_cfg = ctx.obj["config"].get("notifications", {})
    slack_cfg = notify_cfg.get("slack", {})
    if slack_cfg.get("enabled"):
        slack = SlackNotifier(
            token=slack_cfg.get("token"), channel=slack_cfg.get("channel")
        )
        agent.register_notifier("slack", slack)
    email_cfg = notify_cfg.get("email", {})
    if email_cfg.get("enabled"):
        email = EmailNotifier(
            smtp_host=email_cfg.get("smtp_host", ""),
            smtp_port=int(email_cfg.get("smtp_port", 587)),
            username=email_cfg.get("username", ""),
            password=email_cfg.get("password", ""),
            from_addr=email_cfg.get("from", ""),
            to_addr=email_cfg.get("to", ""),
            use_tls=bool(email_cfg.get("use_tls", True)),
        )
        agent.register_notifier("email", email)

    ctx.obj["agent"] = agent


@cli.command()
@click.option("--provider", type=click.Choice(["aws", "azure", "gcp"]), required=True)
@click.option("--start-date", help="Start date for cost analysis (YYYY-MM-DD)")
@click.option("--end-date", help="End date for cost analysis (YYYY-MM-DD)")
@click.option("--output", type=click.Choice(["json", "table"]), default="table")
@click.pass_context
def analyze(ctx, provider, start_date, end_date, output):
    """Analyze cloud costs for a specific provider"""
    agent = ctx.obj["agent"]

    try:
        kwargs = {}
        if start_date:
            kwargs["start_date"] = start_date
        if end_date:
            kwargs["end_date"] = end_date

        cost_data = agent.analyze_costs(provider, **kwargs)

        if output == "json":
            click.echo(json.dumps(cost_data, indent=2, default=str))
        else:
            click.echo(f"\n=== Cost Analysis for {provider.upper()} ===")
            click.echo(f"Total Cost: ${cost_data.get('total_cost', 0):.2f}")
            click.echo(f"Resource Count: {cost_data.get('resource_count', 0)}")
            click.echo(f"Analysis Period: {cost_data.get('period', 'N/A')}")

    except Exception as e:
        click.echo(f"Error analyzing costs: {e}", err=True)
        raise click.Abort() from e


@cli.command()
@click.option("--provider", type=click.Choice(["aws", "azure", "gcp"]), required=True)
@click.option(
    "--strategy", default="cost_optimization", help="Optimization strategy to use"
)
@click.option("--output", type=click.Choice(["json", "table"]), default="table")
@click.pass_context
def optimize(ctx, provider, strategy, output):
    """Run optimization analysis for a specific provider"""
    agent = ctx.obj["agent"]

    try:
        result = agent.optimize(provider, strategy)

        if output == "json":
            # Convert dataclass to dict for JSON serialization
            result_dict = {
                "provider": result.provider,
                "resource_type": result.resource_type,
                "current_cost": result.current_cost,
                "optimized_cost": result.optimized_cost,
                "savings": result.savings,
                "recommendations": result.recommendations,
                "confidence_score": result.confidence_score,
                "timestamp": result.timestamp.isoformat(),
            }
            click.echo(json.dumps(result_dict, indent=2))
        else:
            click.echo(f"\n=== Optimization Results for {result.provider.upper()} ===")
            click.echo(f"Resource Type: {result.resource_type}")
            click.echo(f"Current Cost: ${result.current_cost:.2f}")
            click.echo(f"Optimized Cost: ${result.optimized_cost:.2f}")
            click.echo(
                f"Potential Savings: ${result.savings:.2f} ({result.savings / result.current_cost * 100:.1f}%)"
            )
            click.echo(f"Confidence Score: {result.confidence_score:.1%}")
            click.echo("\nRecommendations:")
            for i, rec in enumerate(result.recommendations, 1):
                click.echo(f"  {i}. {rec}")

    except Exception as e:
        click.echo(f"Error running optimization: {e}", err=True)
        raise click.Abort() from e


@cli.command()
@click.option(
    "--provider",
    type=click.Choice(["aws", "azure", "gcp"]),
    help="Specific provider to get recommendations for",
)
@click.option("--output", type=click.Choice(["json", "table"]), default="table")
@click.pass_context
def recommendations(ctx, provider, output):
    """Get optimization recommendations"""
    agent = ctx.obj["agent"]

    try:
        results = agent.get_recommendations(provider)

        if output == "json":
            results_list = []
            for result in results:
                results_list.append(
                    {
                        "provider": result.provider,
                        "resource_type": result.resource_type,
                        "current_cost": result.current_cost,
                        "optimized_cost": result.optimized_cost,
                        "savings": result.savings,
                        "recommendations": result.recommendations,
                        "confidence_score": result.confidence_score,
                        "timestamp": result.timestamp.isoformat(),
                    }
                )
            click.echo(json.dumps(results_list, indent=2))
        else:
            if not results:
                click.echo("No recommendations available.")
                return

            click.echo("\n=== Cloud Optimization Recommendations ===")
            total_savings = sum(r.savings for r in results)
            click.echo(f"Total Potential Savings: ${total_savings:.2f}")
            click.echo()

            for result in results:
                click.echo(f"{result.provider.upper()}:")
                click.echo(f"  Savings: ${result.savings:.2f}")
                click.echo(f"  Confidence: {result.confidence_score:.1%}")
                click.echo(
                    f"  Top Recommendation: {result.recommendations[0] if result.recommendations else 'None'}"
                )
                click.echo()

    except Exception as e:
        click.echo(f"Error getting recommendations: {e}", err=True)
        raise click.Abort() from e


@cli.group()
def config():
    """Configuration management commands"""
    pass


@config.command()
@click.option("--output", type=click.Path(), help="Output path for sample config")
def init(output):
    """Initialize a sample configuration file"""
    sample_config = {
        "providers": {
            "aws": {"region": "us-east-1", "profile": "default"},
            "azure": {"subscription_id": "your-subscription-id"},
            "gcp": {"project_id": "your-project-id"},
        },
        "integrations": {
            "dataiku": {
                "url": "https://your-dataiku-instance.com",
                "api_key": "your-api-key",
            },
            "databricks": {
                "workspace_url": "https://your-workspace.cloud.databricks.com",
                "token": "your-token",
            },
        },
        "optimization": {
            "strategies": ["cost_optimization"],
            "thresholds": {"min_savings_percent": 10.0, "min_confidence_score": 0.7},
        },
        "llm": {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "api_key": "${OPENAI_API_KEY}",
        },
        "notifications": {
            "slack": {
                "enabled": False,
                "token": "${SLACK_BOT_TOKEN}",
                "channel": "#finops",
            },
            "email": {
                "enabled": False,
                "smtp_host": "smtp.example.com",
                "smtp_port": 587,
                "username": "user",
                "password": "pass",
                "from": "finops@example.com",
                "to": "cloud-team@example.com",
                "use_tls": True,
            },
        },
        "scheduler": {"enabled": False, "interval_minutes": 1440},
    }

    output_path = Path(output) if output else Path("config.yaml")

    import yaml

    with open(output_path, "w") as f:
        yaml.dump(sample_config, f, default_flow_style=False, indent=2)

    click.echo(f"Sample configuration written to {output_path}")


@cli.command()
@click.option(
    "--channels", help="Comma-separated notifier names to use (e.g. slack,email)"
)
@click.option("--provider", type=click.Choice(["aws", "azure", "gcp"]))
@click.pass_context
def proactive(ctx, channels, provider):
    """Run a proactive cycle: analyze -> summarize -> notify"""
    agent = ctx.obj["agent"]
    channel_list = [c.strip() for c in channels.split(",")] if channels else None
    outcome = agent.run_proactive_cycle(provider=provider, channels=channel_list)
    click.echo(outcome["summary"])
    click.echo(f"Notifications sent: {outcome['notify']}")


@cli.command()
# Bind to localhost by default to avoid exposing service broadly (Bandit B104)
@click.option("--host", default="127.0.0.1")
@click.option("--port", default=8000, type=int)
@click.pass_context
def serve(ctx, host, port):
    """Start the FastAPI web server"""
    agent = ctx.obj["agent"]
    # Optionally start scheduler
    sched_cfg = ctx.obj["config"].get("scheduler", {})
    if sched_cfg.get("enabled"):
        scheduler = AgentScheduler(agent)
        scheduler.start(
            interval_minutes=int(sched_cfg.get("interval_minutes", 1440)),
            provider=sched_cfg.get("provider"),
            channels=sched_cfg.get("channels") or None,
        )

    app = create_app(agent)  # reuse configured agent
    uvicorn.run(app, host=host, port=port)


def main():
    """Entry point for CLI"""
    cli()


if __name__ == "__main__":
    main()
