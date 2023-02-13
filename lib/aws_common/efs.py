from typing import Any

from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_efs as efs
from constructs import Construct

from lib.aws_common.ec2 import create_security_group


def build_efs_file_system(
    scope: Construct, vpc: ec2.Vpc, name: str, **kwargs: Any
) -> efs.FileSystem:
    if not kwargs.get("security_group", ""):
        sg = create_security_group(scope=scope, vpc=vpc, name=f"{name}Efs", allow_all_outbound=True)

        # can we better scope to less than the whole vpc?
        sg.add_ingress_rule(ec2.Peer.ipv4(vpc.vpc_cidr_block), ec2.Port.tcp(2049))

    return efs.FileSystem(
        scope,
        f"{name}-fs",
        vpc=vpc,
        lifecycle_policy=efs.LifecyclePolicy.AFTER_14_DAYS,
        out_of_infrequent_access_policy=efs.OutOfInfrequentAccessPolicy.AFTER_1_ACCESS,
        performance_mode=efs.PerformanceMode.GENERAL_PURPOSE,
        **kwargs,
    )
