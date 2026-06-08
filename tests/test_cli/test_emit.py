import json
from uuid import uuid4

from typer.testing import CliRunner

from eventflow.cli import app

runner = CliRunner()


def _valid_order_payload() -> str:
    return json.dumps(
        {
            "order_id": str(uuid4()),
            "customer_id": str(uuid4()),
            "items": [{"sku": "WIDGET-001", "quantity": 2, "price": 24.99}],
            "total_amount": 49.98,
            "shipping_address": "123 Main St, Philadelphia, PA 19103",
        }
    )


def test_emit_local_prints_full_event_chain() -> None:
    result = runner.invoke(
        app,
        ["emit", "--event-type", "order.placed", "--payload", _valid_order_payload()],
    )

    assert result.exit_code == 0
    assert "Running in local mode..." in result.output
    assert "Event chain:" in result.output
    # Full happy-path pipeline fires across all four services.
    for event_type in (
        "order.placed",
        "order.validated",
        "stock.reserved",
        "payment.charged",
        "order.confirmed",
        "customer.notified",
    ):
        assert event_type in result.output
    assert "6 events emitted" in result.output
    assert "Pipeline completed successfully" in result.output


def test_emit_local_defaults_to_local_env() -> None:
    # No --env flag: should run locally, never touching AWS.
    result = runner.invoke(
        app,
        ["emit", "--event-type", "order.placed", "--payload", _valid_order_payload()],
    )
    assert result.exit_code == 0
    assert "local mode" in result.output


def test_emit_unknown_event_type_errors_with_reference() -> None:
    result = runner.invoke(
        app, ["emit", "--event-type", "order.unknown", "--payload", "{}"]
    )
    assert result.exit_code == 1
    assert "Unknown event type 'order.unknown'" in result.output
    assert "ef list-events" in result.output


def test_emit_invalid_json_reports_decode_error() -> None:
    result = runner.invoke(
        app, ["emit", "--event-type", "order.placed", "--payload", "{invalid json}"]
    )
    assert result.exit_code == 1
    assert "Invalid JSON payload" in result.output


def test_emit_validation_failure_lists_missing_fields() -> None:
    result = runner.invoke(
        app,
        ["emit", "--event-type", "order.placed", "--payload", '{"order_id": "abc"}'],
    )
    assert result.exit_code == 1
    assert "Payload validation failed for 'order.placed'" in result.output
    # Per-field errors are surfaced.
    assert "customer_id" in result.output
    assert "total_amount" in result.output
    assert "ef list-events order.placed" in result.output


def test_emit_unknown_env_errors() -> None:
    result = runner.invoke(
        app,
        [
            "emit",
            "--event-type",
            "order.placed",
            "--payload",
            _valid_order_payload(),
            "--env",
            "staging",
        ],
    )
    assert result.exit_code == 1
    assert "Unknown env 'staging'" in result.output


def test_emit_help_displays_usage() -> None:
    result = runner.invoke(app, ["emit", "--help"])
    assert result.exit_code == 0
    assert "--event-type" in result.output
    assert "--payload" in result.output
    assert "--env" in result.output
    assert "--bus-name" in result.output
