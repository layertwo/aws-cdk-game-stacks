import logging
import os

import boto3

logger = logging.getLogger(__name__)


def handler(event, context):
    # get status, but if not found, default to stop
    status = event.get("action", "stop")
    asg = os.environ["AUTOSCALING_GROUP_NAME"]

    logger.info(f"received {status} for {asg}")

    desired_capacity = 0
    if status == "start":
        desired_capacity = 1

    client = boto3.client("autoscaling")
    client.update_auto_scaling_group(
        AutoScalingGroupName=asg,
        DesiredCapacity=desired_capacity,
    )
    logger.info(f"updated desired capacity to {desired_capacity} for autoscaling group {asg}")
