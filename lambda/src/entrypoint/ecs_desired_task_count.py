import logging
import os

import boto3

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def handler(event, context):
    # get status, but if not found, default to stop
    status = event.get("action", "stop")
    cluster_arn = os.environ["ECS_CLUSTER_ARN"]
    service_name = os.environ["ECS_SERVICE_NAME"]

    logger.info(f"received {status} for {cluster_arn} and service {service_name}")

    desired_count = 0
    if status == "start":
        desired_count = 1

    client = boto3.client("ecs")
    client.update_service(cluster=cluster_arn, service=service_name, desiredCount=desired_count)
    logger.info(f"updated desired count to {desired_count} for cluster {cluster_arn}")
