# -*- coding: utf-8 -*-
"""Macro to run a proactive optimization cycle and print a summary."""
from __future__ import annotations

import json
from typing import Any, Dict, List
from textwrap import dedent
from typing import Any, Dict, List

from dataiku import macro_config, plugin_config  # type: ignore

from dataiku_cloud_optimizer import (
    CloudOptimizerAgent,
    AWSProvider,
    AzureProvider,
    GCPProvider,
    CostOptimizationStrategy,
    SimpleLLM,
    SlackNotifier,
    EmailNotifier,
)


def _parse_yaml_config(raw: str | None) -> Dict[str, Any]:
    if not raw:
        return {}
    try:  # pragma: no cover
        import yaml  # type: ignore

        return yaml.safe_load(raw) or {}
    except Exception:
        return {}


def _build_agent(pconf: Dict[str, Any]) -> CloudOptimizerAgent:
    cfg = _parse_yaml_config(pconf.get("default_config_yaml"))
    providers_cfg: Dict[str, Any] = cfg.get("providers", {}) if isinstance(cfg, dict) else {}
    strategies_cfg: Dict[str, Any] = cfg.get("strategies", {}) if isinstance(cfg, dict) else {}

    agent = CloudOptimizerAgent()
    agent.register_provider("aws", AWSProvider(providers_cfg.get("aws")))
    agent.register_provider("azure", AzureProvider(providers_cfg.get("azure")))
    agent.register_provider("gcp", GCPProvider(providers_cfg.get("gcp")))
    cost_cfg = strategies_cfg.get("cost") if isinstance(strategies_cfg, dict) else None
    agent.register_strategy("cost", CostOptimizationStrategy(cost_cfg))
    # Optional LLM (prefer DSS connection)
    llm_connection = pconf.get("llm_connection") or None
    api_key = None if llm_connection else (pconf.get("openai_api_key") or None)
    if llm_connection or api_key:
        model = pconf.get("llm_model") or "gpt-4o-mini"
        max_tokens = int(pconf.get("llm_max_tokens") or 512)
        agent.llm = SimpleLLM(api_key=api_key, model=model, max_tokens=max_tokens, llm_connection=llm_connection)  # type: ignore[attr-defined]
    # Optional notifiers
    if pconf.get("notifications_enabled", True):
        slack_url = pconf.get("slack_webhook_url") or None
        if slack_url:
            agent.register_notifier("slack", SlackNotifier(slack_url))  # type: ignore[attr-defined]
        emails = pconf.get("email_recipients") or ""
        if emails.strip():
            agent.register_notifier("email", EmailNotifier(emails))  # type: ignore[attr-defined]
    return agent


def do(payload: Dict[str, Any]) -> Dict[str, Any]:  # Dataiku macro entrypoint signature
    mconf = macro_config()
    pconf = plugin_config()

    strategies_raw = mconf.get("strategies", "")
    strategies = [s.strip() for s in strategies_raw.split(",") if s.strip()]

    agent = _build_agent(pconf)

    # If strategies empty -> run all registered strategies (here only cost)
    if not strategies:
        strategies = ["cost"]

    results: List[Dict[str, Any]] = []
    for strat in strategies:
        if strat == "cost":
            recs = agent.run_strategy("cost")  # type: ignore[arg-type]
            if isinstance(recs, list):
                for r in recs:
                    if isinstance(r, dict):
                        results.append(r)

    summary = {"strategies_executed": strategies, "recommendations_count": len(results)}

    # LLM summary (optional)
    if getattr(agent, "llm", None):  # type: ignore[attr-defined]
        try:
            context = {"results": results, "strategies": strategies}
            enhanced = agent.llm.summarize(  # type: ignore[attr-defined]
                f"Found {len(results)} recommendations", context
            )
            summary["llm_summary"] = enhanced
        except Exception:
            pass

    # Notifications (optional)
    if agent.notifiers:  # type: ignore[attr-defined]
        msg = summary.get("llm_summary") or f"Recommendations: {len(results)}"
        for name, notifier in agent.notifiers.items():  # type: ignore[attr-defined]
            try:
                notifier.send(msg)
            except Exception:
                pass

    # Macro return format: HTML + JSON sections (simple)
    html_lines = [
        "<h3>Cloud Optimizer Proactive Cycle</h3>",
        f"<p>Strategies: {', '.join(strategies)}</p><p>Recommendations: {len(results)}</p>",
        "<pre style='white-space:pre-wrap;'>" + json.dumps(results, indent=2) + "</pre>",
    ]

    return {
        "result": "\n".join(html_lines),
        "data": summary,
    }


# Dataiku macro loader expects a variable named 'PROCESSOR'
class Processor:  # pragma: no cover - Dataiku harness driven
    def get_input_names(self):  # type: ignore[no-untyped-def]
        return []

    def get_output_names(self):  # type: ignore[no-untyped-def]
        return []

    def run(self, payload):  # type: ignore[no-untyped-def]
        return do(payload)


PROCESSOR = Processor()
