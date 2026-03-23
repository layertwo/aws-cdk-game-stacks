import os
from unittest.mock import MagicMock, patch


def _get_handler():
    with patch.dict(
        os.environ,
        {
            "ECS_CLUSTER_ARN": "arn:aws:ecs:us-east-1:000000000000:cluster/TestCluster",
            "ECS_SERVICE_NAME": "TestService",
        },
    ):
        import ecs_desired_task_count
        return ecs_desired_task_count


_ENV = {
    "ECS_CLUSTER_ARN": "arn:aws:ecs:us-east-1:000000000000:cluster/TestCluster",
    "ECS_SERVICE_NAME": "TestService",
}


def test_stop_action_sets_desired_count_zero(monkeypatch):
    mod = _get_handler()
    ecs_mock = MagicMock()
    for k, v in _ENV.items():
        monkeypatch.setenv(k, v)
    with patch("boto3.client", return_value=ecs_mock):
        import importlib
        importlib.reload(mod)
        mod.handler({"action": "stop"}, None)
    ecs_mock.update_service.assert_called_once_with(
        cluster="arn:aws:ecs:us-east-1:000000000000:cluster/TestCluster",
        service="TestService",
        desiredCount=0,
    )


def test_start_action_sets_desired_count_one(monkeypatch):
    mod = _get_handler()
    ecs_mock = MagicMock()
    for k, v in _ENV.items():
        monkeypatch.setenv(k, v)
    with patch("boto3.client", return_value=ecs_mock):
        import importlib
        importlib.reload(mod)
        mod.handler({"action": "start"}, None)
    ecs_mock.update_service.assert_called_once_with(
        cluster="arn:aws:ecs:us-east-1:000000000000:cluster/TestCluster",
        service="TestService",
        desiredCount=1,
    )


def test_sns_envelope_defaults_to_stop(monkeypatch):
    """SNS delivers a Records envelope with no top-level 'action' key.
    The handler defaults to 'stop', which is the intended watchdog behavior."""
    mod = _get_handler()
    ecs_mock = MagicMock()
    for k, v in _ENV.items():
        monkeypatch.setenv(k, v)
    sns_event = {
        "Records": [
            {
                "EventSource": "aws:sns",
                "Sns": {"Message": "CloudWatch alarm triggered"},
            }
        ]
    }
    with patch("boto3.client", return_value=ecs_mock):
        import importlib
        importlib.reload(mod)
        mod.handler(sns_event, None)
    ecs_mock.update_service.assert_called_once_with(
        cluster="arn:aws:ecs:us-east-1:000000000000:cluster/TestCluster",
        service="TestService",
        desiredCount=0,
    )
