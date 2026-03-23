import json

from src.entrypoint import ecs_webhook

SSM_PATH = "/test/webhook-token"
WEBHOOK_TOKEN = "secret"


def _url_event(body: dict, token: str = WEBHOOK_TOKEN) -> dict:
    return {
        "requestContext": {"http": {"method": "POST"}},
        "headers": {"x-webhook-token": token},
        "body": json.dumps(body),
    }


def _stub_get_token(ssm_stubber, token: str = WEBHOOK_TOKEN):
    ssm_stubber.add_response(
        "get_parameter",
        {"Parameter": {"Value": token}},
        expected_params={"Name": SSM_PATH, "WithDecryption": True},
    )


def test_start_returns_200(ssm_stubber, ecs_stubber, cluster_arn, service_name):
    _stub_get_token(ssm_stubber)
    ecs_stubber.add_response(
        "update_service",
        {},
        expected_params={"cluster": cluster_arn, "service": service_name, "desiredCount": 1},
    )

    resp = ecs_webhook.handler(_url_event({"action": "start"}), None)

    assert resp["statusCode"] == 200
    assert json.loads(resp["body"])["desired_count"] == 1


def test_stop_returns_200(ssm_stubber, ecs_stubber, cluster_arn, service_name):
    _stub_get_token(ssm_stubber)
    ecs_stubber.add_response(
        "update_service",
        {},
        expected_params={"cluster": cluster_arn, "service": service_name, "desiredCount": 0},
    )

    resp = ecs_webhook.handler(_url_event({"action": "stop"}), None)

    assert resp["statusCode"] == 200
    assert json.loads(resp["body"])["desired_count"] == 0


def test_missing_token_returns_403(ssm_stubber):
    _stub_get_token(ssm_stubber)
    event = _url_event({"action": "start"})
    del event["headers"]["x-webhook-token"]

    resp = ecs_webhook.handler(event, None)

    assert resp["statusCode"] == 403


def test_wrong_token_returns_403(ssm_stubber):
    _stub_get_token(ssm_stubber)

    resp = ecs_webhook.handler(_url_event({"action": "start"}, token="wrong"), None)

    assert resp["statusCode"] == 403


def test_invalid_action_returns_400(ssm_stubber):
    _stub_get_token(ssm_stubber)

    resp = ecs_webhook.handler(_url_event({"action": "explode"}), None)

    assert resp["statusCode"] == 400


def test_missing_action_returns_400(ssm_stubber):
    _stub_get_token(ssm_stubber)

    resp = ecs_webhook.handler(_url_event({}), None)

    assert resp["statusCode"] == 400
