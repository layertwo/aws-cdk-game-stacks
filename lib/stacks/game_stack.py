from functools import cached_property

import awsipranges
from aws_cdk import Duration, Stack, Tags
from aws_cdk import aws_autoscaling as autoscaling
from aws_cdk import aws_backup as backup
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_efs as efs
from aws_cdk import aws_events as events
from aws_cdk import aws_events_targets as targets
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_route53 as route53
from constructs import Construct

from lib.aws_common._lambda import build_lambda_function
from lib.aws_common.ec2 import create_security_group
from lib.aws_common.ecs import build_container
from lib.aws_common.iam import ec2_instances_read, ecs_cluster_read_policy, r53_update_policy
from lib.config import GameProperties, PortType


class GameStack(Stack):
    def __init__(self, scope: Construct, props: GameProperties, **kwargs) -> None:
        """Instantiate game stack"""
        super().__init__(scope, f"{props.name.capitalize()}Stack", **kwargs)
        self.props = props

        self.service = self.create_game_service()

        if self.props.auto_start:
            self._create_asg_scheduled_actions()

        if self.props.domain_name:
            self.create_dns_update_lambda()

        # add tags to game stack
        Tags.of(self).add("game", self.props.name.lower())

    def qualify_name(self, name: str) -> str:
        return f"{self.props.name}{name}"

    @cached_property
    def vpc(self) -> ec2.Vpc:
        name = self.qualify_name("Vpc")
        return ec2.Vpc(
            self,
            name,
            vpc_name=name,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name=self.qualify_name("Public"),
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                ),
            ],
            max_azs=99,
        )

    @cached_property
    def cluster(self) -> ecs.Cluster:
        name = self.qualify_name("Cluster")
        cluster = ecs.Cluster(self, name, cluster_name=name, vpc=self.vpc)
        capacity_provider = ecs.AsgCapacityProvider(
            self,
            "AsgCapacityProvider",
            auto_scaling_group=self.asg,
            enable_managed_termination_protection=not self.props.auto_start,
        )
        cluster.add_asg_capacity_provider(capacity_provider)
        return cluster

    @cached_property
    def asg(self) -> autoscaling.AutoScalingGroup:
        name = self.qualify_name("Asg")
        return autoscaling.AutoScalingGroup(
            self,
            name,
            auto_scaling_group_name=name,
            vpc=self.vpc,
            min_capacity=0,
            max_capacity=1,
            new_instances_protected_from_scale_in=False,
            capacity_rebalance=True,
            launch_template=self._launch_template,
        )

    def _create_asg_scheduled_actions(self) -> None:
        autoscaling.ScheduledAction(
            self,
            self.qualify_name("AsgStartAction"),
            auto_scaling_group=self.asg,
            schedule=autoscaling.Schedule.expression(self.props.start_time),
            desired_capacity=1,
        )

        autoscaling.ScheduledAction(
            self,
            self.qualify_name("AsgStopAction"),
            auto_scaling_group=self.asg,
            schedule=autoscaling.Schedule.expression(self.props.stop_time),
            desired_capacity=0,
        )

    @property
    def _launch_template(self) -> ec2.LaunchTemplate:
        instance_type = ec2.InstanceType(self.props.instance_type)
        hardware_type = (
            ecs.AmiHardwareType.ARM
            if instance_type.architecture == ec2.InstanceArchitecture.ARM_64
            else ecs.AmiHardwareType.STANDARD
        )
        name = self.qualify_name("LaunchTemplate")
        return ec2.LaunchTemplate(
            self,
            name,
            launch_template_name=name,
            instance_type=instance_type,
            machine_image=ecs.EcsOptimizedImage.amazon_linux2023(hardware_type),
            security_group=self.instance_security_group,
            spot_options=ec2.LaunchTemplateSpotOptions(
                max_price=0.05, interruption_behavior=ec2.SpotInstanceInterruption.TERMINATE
            ),
            detailed_monitoring=False,
            require_imdsv2=True,
            role=self.instance_role,
            user_data=ec2.UserData.for_linux(),
        )

    @cached_property
    def efs_security_group(self) -> ec2.SecurityGroup:
        """Create game security group with ports from GameProperties"""
        sg = create_security_group(
            scope=self,
            vpc=self.vpc,
            name=self.qualify_name("EfsSecurityGroup"),
            allow_all_outbound=True,
        )

        sg.add_ingress_rule(
            ec2.Peer.security_group_id(self.instance_security_group.security_group_id),
            ec2.Port.tcp(2049),
        )
        return sg

    @cached_property
    def instance_role(self) -> iam.Role:
        return iam.Role(
            self,
            self.qualify_name("InstanceRole"),
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
        )

    @cached_property
    def instance_security_group(self) -> ec2.SecurityGroup:
        """Create game security group with ports from GameProperties"""
        sg = create_security_group(
            scope=self, vpc=self.vpc, name=self.qualify_name("Game"), allow_all_outbound=True
        )
        sg.add_ingress_rule(
            ec2.Peer.any_ipv4(), ec2.Port.icmp_ping(), f"{self.props.name} ICMP from anywhere"
        )
        for port in self.props.ports:
            if port.port_type == PortType.TCP:
                ec2_port = ec2.Port.tcp(port.number)
            elif port.port_type == PortType.UDP:
                ec2_port = ec2.Port.udp(port.number)
            sg.add_ingress_rule(
                ec2.Peer.any_ipv4(),
                ec2_port,
                f"{self.props.name} port {port.port_type.value}/{port.number} from anywhere",
            )

        # Allow EC2 Instance Connect
        if self.props.instance_connect:
            ranges = awsipranges.get_ranges()
            for prefix in ranges.filter(regions=self.region, services="EC2_INSTANCE_CONNECT"):
                ip_range = str(prefix.ip_prefix)
                sg.add_ingress_rule(
                    ec2.Peer.ipv4(ip_range),
                    ec2.Port.all_tcp(),
                    description=f"SSH inbound from EC2 Instance Connect ({prefix.region}) / {ip_range}",
                )
        return sg

    def create_game_service(self) -> ecs.Ec2Service:
        """Create a Ec2Service"""
        self._create_container()
        name = self.qualify_name("Service")
        service = ecs.Ec2Service(
            self,
            name,
            service_name=name,
            cluster=self.cluster,
            task_definition=self.task,
            desired_count=1,
            min_healthy_percent=0,
        )
        service.auto_scale_task_count(max_capacity=1, min_capacity=1)
        return service

    def _create_container(self) -> ecs.ContainerDefinition:
        container = build_container(
            task=self.task,
            # Should this be just the property name?
            name=self.props.name,
            container_image=self.props.container_image,
            cpu=2048,
            memory_limit_mib=self.props.max_mib_memory,
            environment=self.props.environment,
        )
        for port in self.props.ports:
            if port.port_type == PortType.TCP:
                proto = ecs.Protocol.TCP
            elif port.port_type == PortType.UDP:
                proto = ecs.Protocol.UDP
            container.add_port_mappings(
                ecs.PortMapping(container_port=port.number, host_port=port.number, protocol=proto)
            )

        container.add_mount_points(
            ecs.MountPoint(
                container_path=self.props.container_path,
                source_volume=self.ecs_volume.name,
                read_only=False,
            )
        )

    @cached_property
    def task(self) -> ecs.Ec2TaskDefinition:
        """
        Create an ECS task for the specified
        """
        return ecs.Ec2TaskDefinition(
            self,
            self.qualify_name("TaskDef"),
            volumes=[self.ecs_volume],
            network_mode=ecs.NetworkMode.HOST,
        )

    @cached_property
    def file_system(self) -> efs.FileSystem:
        name = self.qualify_name("Efs")
        file_system = efs.FileSystem(
            self,
            name,
            file_system_name=name,
            vpc=self.vpc,
            lifecycle_policy=efs.LifecyclePolicy.AFTER_7_DAYS,
            out_of_infrequent_access_policy=efs.OutOfInfrequentAccessPolicy.AFTER_1_ACCESS,
            performance_mode=efs.PerformanceMode.GENERAL_PURPOSE,
            throughput_mode=efs.ThroughputMode.ELASTIC,
            security_group=self.efs_security_group,
        )
        file_system.add_access_point(name, path="/")

        # backup plan for efs
        # TODO add backup flag to config props
        plan = backup.BackupPlan(
            self,
            self.qualify_name("Backup"),
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
            self.qualify_name("Selection"),
            resources=[backup.BackupResource.from_efs_file_system(file_system)],
        )

        return file_system

    @cached_property
    def ecs_volume(self) -> ecs.Volume:
        """
        Create an efs volume to mount on a container
        """
        return ecs.Volume(
            name=self.qualify_name("Volume"),
            efs_volume_configuration=ecs.EfsVolumeConfiguration(
                file_system_id=self.file_system.file_system_id,
                root_directory="/",
                transit_encryption="ENABLED",
            ),
        )

    @cached_property
    def _ecs_task_rule(self) -> events.Rule:
        """Create a rule to listen for ECS Task State Changes"""
        name = self.qualify_name("EcsRunningTaskRule")
        return events.Rule(
            self,
            name,
            rule_name=name,
            event_pattern=events.EventPattern(
                source=["aws.ecs"],
                detail_type=["ECS Task State Change"],
                detail={
                    "desiredStatus": ["RUNNING"],
                    "lastStatus": ["RUNNING"],
                    "clusterArn": [self.cluster.cluster_arn],
                },
            ),
        )

    @cached_property
    def hosted_zone(self):
        """Import HostedZone into stack for setting DNS"""
        return route53.HostedZone.from_hosted_zone_id(
            self, "HostedZone", hosted_zone_id=self.props.hosted_zone_id
        )

    @cached_property
    def container_instances_arn(self) -> str:
        # setup ARNs for cluster and container instances
        return Stack.of(self).format_arn(
            service="ecs",
            resource="container-instance",
            resource_name=f"{self.cluster.cluster_name}/*",
        )

    @cached_property
    def hostname(self) -> str:
        return (self.props.hostname or self.props.name).lower()

    @cached_property
    def fqdn(self) -> str:
        return f"{self.hostname}.{self.props.domain_name}"

    def create_dns_update_lambda(self) -> _lambda.Function:
        """Lambda that updates route 53 dns"""

        name = self.qualify_name("DnsUpdateLambda")

        function = build_lambda_function(
            scope=self,
            name=name,
            function_name=name,
            handler="ecs_update_r53.handler",
            initial_policy=[
                r53_update_policy(resources=[self.hosted_zone.hosted_zone_arn]),
                ec2_instances_read(resources=["*"]),
                ecs_cluster_read_policy(
                    resources=[
                        self.cluster.cluster_arn,
                        self.service.service_arn,
                        self.container_instances_arn,
                    ]
                ),
            ],
            environment={
                "HOSTNAME": self.hostname,
                "HOSTED_ZONE": self.hosted_zone.hosted_zone_arn,
            },
        )

        self._ecs_task_rule.add_target(
            targets.LambdaFunction(
                handler=function,
            ),
        )
        return function
