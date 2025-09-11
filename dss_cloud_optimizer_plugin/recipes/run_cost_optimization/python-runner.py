# -*- coding: utf-8 -*-
"""Recipe runner for Cloud Cost Optimization.

Reads plugin & recipe params, instantiates the agent with minimal config,
executes optimization, and writes recommendations to the output dataset.
"""
from __future__ import annotations

import json
from textwrap import dedent
from typing import Any, Dict, List
from datetime import datetime, timezone
import uuid

# Dataiku APIs
from dataiku import Dataset  # type: ignore
from dataiku.customrecipe import (  # type: ignore
    get_recipe_config,
    get_plugin_config,
    get_output_names_for_role,
)

# Import agent pieces (assuming the package copied into python-lib)
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
    try:  # pragma: no cover - optional dependency & edge parsing
        import yaml  # type: ignore

        return yaml.safe_load(raw) or {}
    except Exception:
        return {}


def _build_agent(pconf: Dict[str, Any]) -> CloudOptimizerAgent:
    cfg = _parse_yaml_config(pconf.get("default_config_yaml"))
    providers_cfg: Dict[str, Any] = cfg.get("providers", {}) if isinstance(cfg, dict) else {}
    strategies_cfg: Dict[str, Any] = cfg.get("strategies", {}) if isinstance(cfg, dict) else {}

    agent = CloudOptimizerAgent()
    # Providers with optional per-provider configs
    agent.register_provider("aws", AWSProvider(providers_cfg.get("aws")))
    agent.register_provider("azure", AzureProvider(providers_cfg.get("azure")))
    agent.register_provider("gcp", GCPProvider(providers_cfg.get("gcp")))
    # Strategy config
    cost_cfg = strategies_cfg.get("cost") if isinstance(strategies_cfg, dict) else None
    agent.register_strategy("cost", CostOptimizationStrategy(cost_cfg))

    # LLM wiring (prefer DSS LLM connection over direct API key)
    llm_connection = pconf.get("llm_connection") or None
    api_key = None if llm_connection else (pconf.get("openai_api_key") or None)
    if llm_connection or api_key:
        llm_model = pconf.get("llm_model") or "gpt-4o-mini"
        max_tokens = int(pconf.get("llm_max_tokens") or 512)
        agent.llm = SimpleLLM(api_key=api_key, model=llm_model, max_tokens=max_tokens, llm_connection=llm_connection)  # type: ignore[attr-defined]

    # Notifications (optional)
    if pconf.get("notifications_enabled", True):
        slack_url = pconf.get("slack_webhook_url") or None
        if slack_url:
            agent.register_notifier("slack", SlackNotifier(slack_url))  # type: ignore[attr-defined]
        emails = pconf.get("email_recipients") or ""
        if emails.strip():
            agent.register_notifier("email", EmailNotifier(emails))  # type: ignore[attr-defined]
    return agent


def _run_cost_optimization(agent: CloudOptimizerAgent, strategies: List[str]) -> List[Dict[str, Any]]:
    # Currently only one strategy example; extend when multiple.
    results: List[Dict[str, Any]] = []
    for strat in strategies:
        if strat == "cost":
            recs = agent.run_strategy("cost")  # type: ignore[arg-type]
            if isinstance(recs, list):
                for r in recs:
                    if isinstance(r, dict):
                        results.append(r)
    return results


def _write_output(dataset_name: str, rows: List[Dict[str, Any]]) -> None:
    ds = Dataset(dataset_name)
    # Stable default schema for consistency across runs
    default_cols = [
        "provider",
        "resource_id",
        "current_cost",
        "projected_cost",
    "savings_percent",
    "savings",
    "confidence_score",
    "recommendation",
    # run metadata
    "run_id",
    "run_timestamp",
    "strategy",
    "total_savings",
    ]
    # Infer columns from union of keys, fallback to defaults when empty
    all_keys: List[str] = []
    seen = set()
    for r in rows:
        for k in r.keys():
            if k not in seen:
                seen.add(k)
                all_keys.append(k)
    if not all_keys:
        all_keys = default_cols
    # Prefer numeric types for known numeric fields
    numeric_fields = {"current_cost", "projected_cost", "savings", "savings_percent", "confidence", "confidence_score", "total_savings"}
    schema = [
        {"name": k, "type": ("double" if k in numeric_fields else "string")}
        for k in all_keys
    ]
    ds.write_schema(schema)

    # Normalize rows to schema keys and string types
    to_write: List[Dict[str, Any]] = []
    if rows:
        for r in rows:
            row_out = {}
            for k in all_keys:
                v = r.get(k)
                if k in {"current_cost", "projected_cost", "savings", "savings_percent", "confidence", "confidence_score", "total_savings"}:
                    try:
                        row_out[k] = None if v is None or v == "" else float(v)
                    except Exception:
                        row_out[k] = None
                else:
                    row_out[k] = "" if v is None else str(v)
            to_write.append(row_out)
    else:
        to_write = [{k: (0.0 if k in {"current_cost", "projected_cost", "savings", "savings_percent", "confidence", "confidence_score", "total_savings"} else "") for k in all_keys}]
        to_write[0]["recommendation"] = "No recommendations generated in this run"

    with ds.get_writer() as w:
        for r in to_write:
            w.write_row_dict(r)


def main() -> None:
    rconf = get_recipe_config()
    pconf = get_plugin_config()

    strategies_raw = rconf.get("strategies", "cost")
    strategies = [s.strip() for s in strategies_raw.split(",") if s.strip()] or ["cost"]

    # Resolve output dataset with robust fallbacks
    output_names = []
    try:
        output_names = get_output_names_for_role("main") or []
    except Exception as e:  # pragma: no cover - defensive
        print("DEBUG: get_output_names_for_role('main') failed:", e)
    if not output_names:
        for role in ("output", "out", "default", "dataset", "result"):
            try:
                cand = get_output_names_for_role(role)
                if cand:
                    print(f"DEBUG: Found outputs via role '{role}': {cand}")
                    output_names = cand
                    break
            except Exception:
                pass
    if not output_names:
        try:
            from dataiku import get_recipe_output_names  # type: ignore

            mapping = get_recipe_output_names()
            print("DEBUG: get_recipe_output_names mapping:", mapping)
            for key, names in mapping.items():
                if names:
                    print(f"DEBUG: Using role '{key}' with outputs {names}")
                    output_names = names
                    break
        except Exception as e:
            print("DEBUG: get_recipe_output_names failed:", e)
    if not output_names:
        raise RuntimeError(
            "No output dataset configured for this recipe (tried roles: main, output, out, default)"
        )
    output_ds = output_names[0]

    agent = _build_agent(pconf)
    recs = _run_cost_optimization(agent, strategies)

    # Serialize nested objects to JSON strings for consistency
    serializable_rows: List[Dict[str, Any]] = []
    # Compute run metadata
    run_id = str(uuid.uuid4())
    run_ts = datetime.now(timezone.utc).isoformat()
    strategy_label = ",".join(strategies)

    def _num(x: Any) -> float:
        try:
            return float(x)
        except Exception:
            return 0.0

    def _savings_value(r: Dict[str, Any]) -> float:
        if "savings" in r and r["savings"] is not None:
            try:
                return float(r["savings"])  # absolute
            except Exception:
                pass
        # try percent of current_cost
        sp = r.get("savings_percent")
        cc = r.get("current_cost")
        pc = r.get("projected_cost")
        if sp is not None and cc is not None:
            try:
                return float(cc) * float(sp) / 100.0
            except Exception:
                pass
        if cc is not None and pc is not None:
            try:
                return float(cc) - float(pc)
            except Exception:
                pass
        return 0.0

    # Normalize rows and attach metadata
    for r in recs:
        row: Dict[str, Any] = {}
        for k, v in r.items():
            if isinstance(v, (dict, list)):
                row[k] = json.dumps(v)
            else:
                row[k] = v
        # Attach run metadata (will be added to schema in writer)
        row["run_id"] = run_id
        row["run_timestamp"] = run_ts
        row["strategy"] = strategy_label
        serializable_rows.append(row)

    # Sort by best savings
    serializable_rows.sort(key=_savings_value, reverse=True)

    # Total savings for the run (repeat per-row for convenience)
    total_savings = sum(_savings_value(r) for r in serializable_rows)
    for r in serializable_rows:
        r["total_savings"] = total_savings

    # Emit output (optionally with placeholder if empty)
    emit_placeholder = bool(rconf.get("emit_placeholder_on_empty", True))
    if serializable_rows or emit_placeholder:
        # Ensure placeholder rows also carry metadata
        if not serializable_rows:
            serializable_rows = [{
                "run_id": run_id,
                "run_timestamp": run_ts,
                "strategy": strategy_label,
                "total_savings": 0.0,
                "recommendation": "No recommendations generated in this run",
            }]
        _write_output(output_ds, serializable_rows)

    # Optional summary & notify (if configured)
    if getattr(agent, "llm", None) or agent.notifiers:  # type: ignore[attr-defined]
        # Construct simple results object shape for summarization
        try:
            summary_base = f"Produced {len(serializable_rows)} recommendations across strategies {','.join(strategies)}"
            if getattr(agent, "llm", None):
                context = {"count": len(serializable_rows), "strategies": strategies}
                final_summary = agent.llm.summarize(summary_base, context)  # type: ignore[attr-defined]
            else:
                final_summary = summary_base
            if agent.notifiers:  # type: ignore[attr-defined]
                for name, notifier in agent.notifiers.items():  # type: ignore[attr-defined]
                    try:
                        notifier.send(final_summary)
                    except Exception:
                        pass
        except Exception:
            pass


if __name__ == "__main__":  # pragma: no cover
    main()
