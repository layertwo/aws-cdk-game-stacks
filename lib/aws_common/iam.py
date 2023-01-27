from typing import List

from aws_cdk import aws_iam as iam


def ecs_cluster_read_policy(resources: List) -> iam.PolicyStatement:
    """Create policy to read details about cluster and service"""
    return iam.PolicyStatement(
        effect=iam.Effect.ALLOW,
        actions=[
            "ecs:ListClusters",
            "ecs:DescribeClusters",
            "ecs:ListTasks",
            "ecs:DescribeTasks",
            "ecs:ListServices",
            "ecs:DescribeServices",
            "ecs:DescribeContainerInstances",
            "ecs:DescribeTaskDefinition",
        ],
        resources=resources,
    )


def ecs_cluster_update_policy(resources: List) -> iam.PolicyStatement:
    """Allow service to update cluster"""
    return iam.PolicyStatement(
        effect=iam.Effect.ALLOW,
        actions=[
            "ecs:UpdateService",
        ],
        resources=resources,
    )


def ec2_instances_read(resources: List) -> iam.PolicyStatement:
    """Policy for reading ENI information"""
    return iam.PolicyStatement(
        effect=iam.Effect.ALLOW,
        actions=["ec2:DescribeInstances", "ec2:DescribeNetworkInterfaces"],
        resources=resources,
    )


def r53_update_policy(resources: List) -> iam.PolicyStatement:
    """Create statement for updating DNS"""
    return iam.PolicyStatement(
        effect=iam.Effect.ALLOW,
        actions=[
            "route53:GetHostedZone",
            "route53:ChangeResourceRecordSets",
            "route53:ListHostedZones",
        ],
        resources=resources,
    )


def asg_update_policy(resources: List) -> iam.PolicyStatement:
    """Allow service to update autoscaling group"""
    return iam.PolicyStatement(
        effect=iam.Effect.ALLOW,
        actions=[
            "autoscaling:UpdateAutoScalingGroup",
        ],
        resources=resources,
    )
