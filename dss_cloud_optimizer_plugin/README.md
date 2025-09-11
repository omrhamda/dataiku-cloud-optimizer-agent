# Cloud Optimizer Dataiku Plugin

Embedded version of the Cloud Optimizer Agent as a Dataiku plugin.

## Components
- Recipe: Run Cloud Cost Optimization -> outputs dataset of recommendations
- Macro: Run Proactive Cycle -> on-demand run & HTML summary

## Installation
1. Zip the folder contents (plugin root).
2. Upload in Dataiku DSS: Administration > Plugins > Upload.
3. Create a Python code env for the plugin; install required deps (manually mirror project minimal deps).

## Configuration
- Optional YAML config (paste into plugin settings) merges with runtime defaults (not yet auto-parsed in this skeleton).
- Provide cloud credentials through DSS connections or project variables.
- OpenAI key (optional) via secure plugin param.

## Extending
- Add more strategies under `python-lib/dataiku_cloud_optimizer/strategies/` and register in both recipe & macro builders.
- Add notifiers or integrations similarly and wire them before executing strategies.

## Notes
This skeleton intentionally trims features (web server, scheduler) in favor of DSS-managed scheduling via Scenarios.
