import importlib
import json
import os
from unittest.mock import MagicMock, patch


# Helper to build a Function URL event
def _url_event(body: dict, token: str = "secret") -> dict:
    return {
        "requestContext": {"http": {"method": "POST"}},
        "headers": {"x-webhook-token": token},
        "body": json.dumps(body),
    }


def _load_handler(ssm_token: str = "secret"):
    """Import ecs_webhook with a mocked SSM client returning ssm_token."""
    ssm_mock = MagicMock()
    ssm_mock.get_parameter.return_value = {"Parameter": {"Value": ssm_token}}
    boto3_mock = MagicMock()
    boto3_mock.client.return_value = ssm_mock

    with patch.dict(
        os.environ,
        {
            "ECS_CLUSTER_ARN": "arn:aws:ecs:us-east-1:000000000000:cluster/TestCluster",
            "ECS_SERVICE_NAME": "TestService",
            "WEBHOOK_TOKEN_SSM_PATH": "/test/webhook-token",
        },
    ):
        with patch("boto3.client", return_value=ssm_mock):
            from src.entrypoint import ecs_webhook

            importlib.reload(ecs_webhook)
            ecs_webhook._token = ssm_token  # inject cached token
    return ecs_webhook


def test_start_returns_200(monkeypatch):
    mod = _load_handler()
    ecs_mock = MagicMock()
    monkeypatch.setattr(mod, "_ecs_client", ecs_mock)
    monkeypatch.setenv("ECS_CLUSTER_ARN", "arn:aws:ecs:us-east-1:000000000000:cluster/TestCluster")
    monkeypatch.setenv("ECS_SERVICE_NAME", "TestService")

    resp = mod.handler(_url_event({"action": "start"}), None)

    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert body["desired_count"] == 1
    ecs_mock.update_service.assert_called_once()


def test_stop_returns_200(monkeypatch):
    mod = _load_handler()
    ecs_mock = MagicMock()
    monkeypatch.setattr(mod, "_ecs_client", ecs_mock)
    monkeypatch.setenv("ECS_CLUSTER_ARN", "arn:aws:ecs:us-east-1:000000000000:cluster/TestCluster")
    monkeypatch.setenv("ECS_SERVICE_NAME", "TestService")

    resp = mod.handler(_url_event({"action": "stop"}), None)

    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert body["desired_count"] == 0


def test_missing_token_returns_403(monkeypatch):
    mod = _load_handler()
    ecs_mock = MagicMock()
    monkeypatch.setattr(mod, "_ecs_client", ecs_mock)
    event = _url_event({"action": "start"})
    del event["headers"]["x-webhook-token"]

    resp = mod.handler(event, None)

    assert resp["statusCode"] == 403
    ecs_mock.update_service.assert_not_called()


def test_wrong_token_returns_403(monkeypatch):
    mod = _load_handler()
    ecs_mock = MagicMock()
    monkeypatch.setattr(mod, "_ecs_client", ecs_mock)
    event = _url_event({"action": "start"}, token="wrong")

    resp = mod.handler(event, None)

    assert resp["statusCode"] == 403
    ecs_mock.update_service.assert_not_called()


def test_invalid_action_returns_400(monkeypatch):
    mod = _load_handler()
    ecs_mock = MagicMock()
    monkeypatch.setattr(mod, "_ecs_client", ecs_mock)

    resp = mod.handler(_url_event({"action": "explode"}), None)

    assert resp["statusCode"] == 400
    ecs_mock.update_service.assert_not_called()


def test_missing_action_returns_400(monkeypatch):
    mod = _load_handler()
    ecs_mock = MagicMock()
    monkeypatch.setattr(mod, "_ecs_client", ecs_mock)

    resp = mod.handler(_url_event({}), None)

    assert resp["statusCode"] == 400
