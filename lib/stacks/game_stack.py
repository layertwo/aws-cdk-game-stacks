from functools import cached_property

from aws_cdk import Duration, Stack
from aws_cdk import aws_autoscaling as autoscaling
from aws_cdk import aws_backup as backup
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_efs as efs
from aws_cdk import aws_events as events
from aws_cdk import aws_events_targets as targets
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_route53 as route53
from constructs import Construct

from lib.aws_common._lambda import build_lambda_function
from lib.aws_common.ec2 import create_security_group
from lib.aws_common.ecs import build_container, build_ecs_efs_volume
from lib.aws_common.efs import build_efs_file_system
from lib.aws_common.iam import (
    asg_update_policy,
    ec2_instances_read,
    ecs_cluster_read_policy,
    ecs_cluster_update_policy,
    r53_update_policy,
)
from lib.config import GameProperties


class GameStack(Stack):
    def __init__(self, scope: Construct, props: GameProperties, **kwargs) -> None:
        """Instantiate game stack"""
        super().__init__(scope, f"{props.name.capitalize()}Stack", **kwargs)
        self.props = props

        # setup VPC
        self.vpc = ec2.Vpc(
            self,
            f"{props.name}Vpc",
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name=f"{props.name}Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                ),
            ],
        )
        self.cluster = ecs.Cluster(self, f"{self.props.name}Cluster", vpc=self.vpc)
        capacity_provider = ecs.AsgCapacityProvider(
            self, "AsgCapacityProvider", auto_scaling_group=self.asg
        )
        self.cluster.add_asg_capacity_provider(capacity_provider)

        self.service = self.create_service()

        if self.props.auto_start:
            self.create_lambda_start_stop_rule(enabled=self.props.auto_start)

        if self.props.hosted_zone:
            self.create_dns_update_lambda()

    @cached_property
    def asg(self) -> autoscaling.AutoScalingGroup:
        return autoscaling.AutoScalingGroup(
            self,
            f"{self.props.name}Asg",
            vpc=self.vpc,
            min_capacity=0,
            max_capacity=1,
            instance_type=ec2.InstanceType("t3a.large"),
            machine_image=ecs.EcsOptimizedImage.amazon_linux2(),
            security_group=self.game_security_group,
            spot_price="0.03",
            instance_monitoring=autoscaling.Monitoring.BASIC,
            new_instances_protected_from_scale_in=False,
        )

    @cached_property
    def game_efs_security_group(self) -> ec2.SecurityGroup:
        """Create game security group with ports from GameProperties"""
        sg = create_security_group(
            scope=self, vpc=self.vpc, name=f"{self.props.name}Efs", allow_all_outbound=True
        )

        sg.add_ingress_rule(
            ec2.Peer.security_group_id(self.game_security_group.security_group_id),
            ec2.Port.tcp(2049),
        )
        return sg

    @cached_property
    def game_security_group(self) -> ec2.SecurityGroup:
        """Create game security group with ports from GameProperties"""
        sg = create_security_group(
            scope=self, vpc=self.vpc, name=f"{self.props.name}Game", allow_all_outbound=True
        )
        for port in self.props.tcp_ports:
            sg.add_ingress_rule(
                ec2.Peer.any_ipv4(),
                ec2.Port.tcp(port),
                f"{self.props.name} port tcp/{port} from anywhere",
            )

        for port in self.props.udp_ports:
            sg.add_ingress_rule(
                ec2.Peer.any_ipv4(),
                ec2.Port.udp(port),
                f"{self.props.name} port udp/{port} from anywhere",
            )
        return sg

    def create_service(self) -> ecs.Ec2Service:
        """Create a Ec2Service"""
        service = ecs.Ec2Service(
            self,
            f"{self.props.name}-service",
            cluster=self.cluster,
            task_definition=self._create_task(),
            desired_count=0,
        )
        service.auto_scale_task_count(max_capacity=1, min_capacity=1)
        return service

    def _create_task(self) -> ecs.Ec2TaskDefinition:
        """
        Create an ECS task for the specified
        """
        volume = self.create_efs_volume(self.props.name)
        task = ecs.Ec2TaskDefinition(
            self, f"{self.props.name}-td", volumes=[volume], network_mode=ecs.NetworkMode.HOST
        )
        container = build_container(
            task=task,
            name=self.props.name,
            container_image=self.props.container_image,
            cpu=2048,
            memory_limit_mib=6144,
            environment=self.props.environment,
        )
        for port in self.props.tcp_ports:
            container.add_port_mappings(
                ecs.PortMapping(container_port=port, host_port=port, protocol=ecs.Protocol.TCP)
            )

        for port in self.props.udp_ports:
            container.add_port_mappings(
                ecs.PortMapping(container_port=port, host_port=port, protocol=ecs.Protocol.UDP)
            )

        container.add_mount_points(
            ecs.MountPoint(
                container_path=self.props.container_path,
                source_volume=volume.name,
                read_only=False,
            )
        )
        return task

    def _create_efs_backup(self, name: str, file_system: efs.FileSystem) -> backup.BackupPlan:
        plan = backup.BackupPlan(
            self,
            f"{name}Backup",
            backup_plan_rules=[
                backup.BackupPlanRule(
                    schedule_expression=events.Schedule.cron(
                        minute="0", hour="9", week_day="SAT,SUN,MON"
                    ),
                    move_to_cold_storage_after=Duration.days(14),
                )
            ],
        )
        plan.add_selection(
            f"{name}Selection", resources=[backup.BackupResource.from_efs_file_system(file_system)]
        )
        return plan

    def create_efs_volume(self, name: str) -> ecs.Volume:
        """
        Create an efs volume to mount on a container
        """
        file_system = build_efs_file_system(
            scope=self,
            name=name,
            vpc=self.vpc,
            throughput_mode=efs.ThroughputMode.ELASTIC,
            security_group=self.game_efs_security_group,
        )
        file_system.add_access_point(name, path="/")

        # setup backup for efs
        self._create_efs_backup(name, file_system)

        # define an ECS volume for this filesystem
        return build_ecs_efs_volume(file_system=file_system, name=name)

    @cached_property
    def _ecs_task_rule(self) -> events.Rule:
        """Create a rule to listen for ECS Task State Changes"""
        return events.Rule(
            self,
            f"{self.props.name}EcsRunningTaskRule",
            event_pattern=events.EventPattern(
                source=["aws.ecs"],
                detail_type=["ECS Task State Change"],
                detail={"desiredStatus": ["RUNNING"], "lastStatus": ["RUNNING"]},
            ),
        )

    @cached_property
    def hosted_zone(self):
        """Import HostedZone into stack for setting DNS"""
        return route53.HostedZone.from_hosted_zone_id(
            self, "HostedZone", self.props.hosted_zone
        )

    def create_dns_update_lambda(self) -> _lambda.Function:
        """Lambda that updates route 53 dns"""
        name = f"{self.props.name}DnsUpdateLambda"
        function = build_lambda_function(
            scope=self,
            name=name,
            function_name=name,
            handler="ecs_update_r53.handler",
            initial_policy=[
                r53_update_policy(resources=[self.hosted_zone.hosted_zone_arn]),
                ec2_instances_read(resources=["*"]),
                ecs_cluster_read_policy(resources=[self.cluster.cluster_arn]),
            ],
        )
        hostname = self.props.hostname or self.props.name
        self._ecs_task_rule.add_target(
            targets.LambdaFunction(
                handler=function,
                event=events.RuleTargetInput.from_object(
                    {"hostname": hostname.lower(), "hosted_zone": self.hosted_zone.hosted_zone_arn}
                ),
            ),
        )
        return function

    @cached_property
    def ecs_update_lambda(self) -> _lambda.Function:
        """Lambda that updates cluster desired count"""
        name = f"{self.props.name}ClusterUpdateLambda"
        return build_lambda_function(
            scope=self,
            name=name,
            function_name=name,
            handler="ecs_desired_task_count.handler",
            initial_policy=[
                ecs_cluster_read_policy(resources=[self.cluster.cluster_arn]),
                ecs_cluster_update_policy(resources=[self.cluster.cluster_arn]),
            ],
        )

    @cached_property
    def asg_update_lambda(self) -> _lambda.Function:
        """Lambda that updates autoscaling group desired count"""
        name = f"{self.props.name}AsgUpdateLambda"
        return build_lambda_function(
            scope=self,
            name=name,
            function_name=name,
            handler="asg_set_desired_capacity.handler",
            initial_policy=[
                asg_update_policy(resources=[self.asg.auto_scaling_group_arn]),
            ],
        )

    def create_lambda_start_stop_rule(
        self,
        enabled: bool,
    ) -> None:
        """Lambda that updates cluster desired count"""

        rule_config = {
            "start": events.Schedule.cron(minute="0", hour="23", week_day="FRI"),  # Friday 3PM PST
            "stop": events.Schedule.cron(minute="0", hour="6", week_day="MON"),  # Sunday 10PM PST
        }

        for action, schedule in rule_config.items():
            events.Rule(
                self,
                f"{self.props.name}{action.capitalize()}Rule",
                schedule=schedule,
                enabled=enabled,
                targets=[
                    targets.LambdaFunction(
                        handler=self.ecs_update_lambda,
                        event=events.RuleTargetInput.from_object(
                            {
                                "action": action,
                                "cluster": self.cluster.cluster_arn,
                                "service_name": self.service.service_name,
                            }
                        ),
                    ),
                    targets.LambdaFunction(
                        handler=self.asg_update_lambda,
                        event=events.RuleTargetInput.from_object(
                            {"action": action, "asg": self.asg.auto_scaling_group_name}
                        ),
                    ),
                ],
            )
