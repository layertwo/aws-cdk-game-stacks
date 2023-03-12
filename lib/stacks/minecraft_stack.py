from aws_cdk import Duration
from aws_cdk import aws_route53 as route53
from constructs import Construct

from lib.config import GameProperties
from lib.stacks.game_stack import GameStack


class MinecraftStack(GameStack):
    def __init__(self, scope: Construct, props: GameProperties, **kwargs) -> None:
        """Minecraft Stack"""
        super().__init__(scope, props, **kwargs)
        self.minecraft_srv_record()

    def minecraft_srv_record(self) -> route53.SrvRecord:
        record = route53.SrvRecord(
            self,
            "MinecraftSrvRecord",
            values=[
                route53.SrvRecordValue(host_name=self.hostname, port=25565, priority=0, weight=0)
            ],
            zone=self.hosted_zone,
            record_name=f"_minecraft._tcp.{self.hostname}",
            ttl=Duration.seconds(60),
        )
        return record
