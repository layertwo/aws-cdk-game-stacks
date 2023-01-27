from typing import Any

from aws_cdk import Duration
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_logs as logs


def build_lambda_function(scope, name: str, handler: str, **kwargs: Any) -> _lambda.Function:
    return _lambda.Function(
        scope=scope,
        id=name,
        runtime=_lambda.Runtime.PYTHON_3_9,
        code=_lambda.Code.from_asset("./lambda"),
        handler=handler,
        timeout=Duration.minutes(1),
        log_retention=logs.RetentionDays.ONE_WEEK,
        **kwargs,
    )
