import hmac
import json
import logging
import os

import boto3

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Module-level cache — populated on cold start
_token: str = ""
_ecs_client = boto3.client("ecs")


def _load_token() -> str:
    global _token
    if _token:
        return _token
    ssm = boto3.client("ssm")
    resp = ssm.get_parameter(
        Name=os.environ["WEBHOOK_TOKEN_SSM_PATH"],
        WithDecryption=True,
    )
    _token = resp["Parameter"]["Value"]
    return _token


def _response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def handler(event, context) -> dict:
    # Function URL events have requestContext.http; other invocations do not.
    is_url_invocation = bool(event.get("requestContext", {}).get("http"))

    if is_url_invocation:
        headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
        provided = headers.get("x-webhook-token", "")
        expected = _load_token()
        if not hmac.compare_digest(provided, expected):
            logger.warning("Rejected request: invalid or missing token")
            return _response(403, {"error": "forbidden"})

        try:
            body = json.loads(event.get("body") or "{}")
        except (json.JSONDecodeError, TypeError):
            return _response(400, {"error": "invalid body"})
        action = body.get("action")
    else:
        # Internal invocation (e.g. direct Lambda invoke with {"action": "start"})
        action = event.get("action", "stop")

    if action not in ("start", "stop"):
        return _response(400, {"error": "invalid action"})

    desired_count = 1 if action == "start" else 0
    cluster_arn = os.environ["ECS_CLUSTER_ARN"]
    service_name = os.environ["ECS_SERVICE_NAME"]

    logger.info(f"action={action} desired_count={desired_count} service={service_name}")
    _ecs_client.update_service(
        cluster=cluster_arn,
        service=service_name,
        desiredCount=desired_count,
    )

    return _response(200, {"status": "ok", "desired_count": desired_count})
