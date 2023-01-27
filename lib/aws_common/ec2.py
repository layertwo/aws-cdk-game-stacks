from typing import Any

from aws_cdk import aws_ec2 as ec2
from constructs import Construct


def create_security_group(
    scope: Construct, vpc: ec2.Vpc, name: str, **kwargs: Any
) -> ec2.SecurityGroup:
    return ec2.SecurityGroup(
        scope,
        f"{name}SecurityGroup",
        vpc=vpc,
        description=f"{name.capitalize()} security group",
        **kwargs,
    )
