import hmac
import json
import logging
import os
from functools import lru_cache

import boto3
import botocore.exceptions

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@lru_cache
def _load_token(ssm_client) -> str:
    try:
        resp = ssm_client.get_parameter(
            Name=os.environ["WEBHOOK_TOKEN_SSM_PATH"],
            WithDecryption=True,
        )
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "ParameterNotFound":
            logger.error(
                "Webhook token not configured. Run: aws ssm put-parameter "
                "--name %s --type SecureString --value <your-secret>",
                os.environ["WEBHOOK_TOKEN_SSM_PATH"],
            )
            return ""  # empty string — compare_digest("", expected) returns False → 403
        raise
    return resp["Parameter"]["Value"]


def _response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def handler(event, context) -> dict:

    session = boto3.Session()
    ecs_client = session.client("ecs")
    ssm_client = session.client("ssm")
    # Function URL events have requestContext.http; other invocations do not.
    is_url_invocation = bool(event.get("requestContext", {}).get("http"))

    if is_url_invocation:
        headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
        provided = headers.get("x-webhook-token", "")
        expected = _load_token(ssm_client)
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
    ecs_client.update_service(
        cluster=cluster_arn,
        service=service_name,
        desiredCount=desired_count,
    )

    desired_count_ssm_path = os.environ.get("DESIRED_COUNT_SSM_PATH")
    if desired_count_ssm_path:
        ssm_client.put_parameter(
            Name=desired_count_ssm_path,
            Value=str(desired_count),
            Type="String",
            Overwrite=True,
        )
        logger.info(f"updated {desired_count_ssm_path} to {desired_count}")

    return _response(200, {"status": "ok", "desired_count": desired_count})
