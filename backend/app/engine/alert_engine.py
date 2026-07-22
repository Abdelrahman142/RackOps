from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class EvaluationResult:
    triggered: bool
    rule_id: str | None = None
    device_id: str | None = None
    metric_key: str | None = None
    value: float | None = None
    threshold: float | None = None
    condition: str | None = None
    severity: str | None = None


COMPARISON_OPS = {
    "GREATER_THAN": lambda v, t: v > t,
    "LESS_THAN": lambda v, t: v < t,
    "EQUAL": lambda v, t: v == t,
    "NOT_EQUAL": lambda v, t: v != t,
}


class AlertEngine:
    def __init__(self):
        self._rules = []
        self._evaluations = []

    def evaluate_rule(
        self,
        rule_id: str,
        metric_key: str,
        value: float,
        threshold: float,
        condition: str,
        severity: str,
    ) -> EvaluationResult:
        op = COMPARISON_OPS.get(condition)

        if op is None:
            return EvaluationResult(
                triggered=False,
            )

        triggered = op(value, threshold)

        return EvaluationResult(
            triggered=triggered,
            rule_id=rule_id,
            metric_key=metric_key,
            value=value,
            threshold=threshold,
            condition=condition,
            severity=severity,
        )

    def evaluate_rules_for_metric(
        self,
        rules: list,
        metric_key: str,
        value: float,
        device_id: str,
    ) -> list[EvaluationResult]:
        results = []

        for rule in rules:
            if rule.metric_key != metric_key:
                continue

            if not rule.enabled:
                continue

            result = self.evaluate_rule(
                rule_id=str(rule.id),
                metric_key=metric_key,
                value=value,
                threshold=rule.threshold_value,
                condition=rule.condition,
                severity=rule.severity,
            )
            result.device_id = device_id

            if result.triggered:
                results.append(result)

        return results

    def determine_severity(
        self,
        value: float,
        warning_threshold: float,
        critical_threshold: float,
    ) -> str:
        if value >= critical_threshold:
            return "CRITICAL"
        if value >= warning_threshold:
            return "WARNING"
        return "INFO"

    def build_alert_title(
        self,
        rule_name: str,
        device_id: str,
        value: float,
        condition: str,
        threshold: float,
    ) -> str:
        condition_symbols = {
            "GREATER_THAN": ">",
            "LESS_THAN": "<",
            "EQUAL": "==",
            "NOT_EQUAL": "!=",
        }
        symbol = condition_symbols.get(
            condition, condition
        )
        return (
            f"{rule_name}: {value}{symbol}{threshold} "
            f"(device {device_id[:8]}...)"
        )

    def build_alert_description(
        self,
        metric_key: str,
        value: float,
        condition: str,
        threshold: float,
        severity: str,
    ) -> str:
        condition_symbols = {
            "GREATER_THAN": ">",
            "LESS_THAN": "<",
            "EQUAL": "==",
            "NOT_EQUAL": "!=",
        }
        symbol = condition_symbols.get(
            condition, condition
        )
        return (
            f"Metric '{metric_key}' value {value} "
            f"{symbol} threshold {threshold}. "
            f"Severity: {severity}"
        )
