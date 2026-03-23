from src.entrypoint import ecs_desired_task_count


def test_stop_action_sets_desired_count_zero(cluster_arn, service_name, ecs_stubber):
    ecs_stubber.add_response(
        "update_service",
        {},
        expected_params={
            "cluster": cluster_arn,
            "service": service_name,
            "desiredCount": 0,
        },
    )
    ecs_desired_task_count.handler({"action": "stop"}, None)


def test_start_action_sets_desired_count_one(cluster_arn, service_name, ecs_stubber):
    ecs_stubber.add_response(
        "update_service",
        {},
        expected_params={
            "cluster": cluster_arn,
            "service": service_name,
            "desiredCount": 1,
        },
    )
    ecs_desired_task_count.handler({"action": "start"}, None)


def test_sns_envelope_defaults_to_stop(cluster_arn, service_name, ecs_stubber):
    """SNS delivers a Records envelope with no top-level 'action' key.
    The handler defaults to 'stop', which is the intended watchdog behavior."""
    ecs_stubber.add_response(
        "update_service",
        {},
        expected_params={
            "cluster": cluster_arn,
            "service": service_name,
            "desiredCount": 0,
        },
    )
    sns_event = {
        "Records": [
            {
                "EventSource": "aws:sns",
                "Sns": {"Message": "CloudWatch alarm triggered"},
            }
        ]
    }
    ecs_desired_task_count.handler(sns_event, None)
