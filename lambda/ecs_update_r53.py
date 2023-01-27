import logging
import os
from typing import List

from boto3.session import Session

logger = logging.getLogger(__name__)


def handler(event, context) -> None:
    """Update DNS for Fargate Container"""
    session = Session()
    hostname = os.environ["HOSTNAME"]
    hosted_zone = os.environ["HOSTED_ZONE"]

    eni = get_eni_id(attachments=event["detail"]["attachments"])
    ip = get_eip_from_eni(session=session, eni=eni)
    domain = get_hosted_zone_domain(session=session, hosted_zone=hosted_zone)

    logging.info(f"Found IP {ip} for DNS record ({hostname}) in domain {domain}")
    fqdn = f"{hostname}.{domain}"
    update_dns_with_ip(
        session=session,
        hosted_zone=hosted_zone,
        fqdn=fqdn,
        ip=ip,
    )
    logger.info(f"Set {fqdn} to IP {ip} in hosted zone {hosted_zone}")


def get_eni_id(attachments: List) -> str:
    """Get ENI ID from ECS task"""
    for a in attachments:
        if a["type"] in ("ElasticNetworkInterface", "eni"):
            for d in a.get("details", []):
                if d["name"] == "networkInterfaceId":
                    return d["value"]
    return ""


def get_eip_from_eni(session: Session, eni: str) -> str:
    client = session.client("ec2")
    response = client.describe_network_interfaces(
        NetworkInterfaceIds=[eni],
    )
    for n in response["NetworkInterfaces"]:
        return n["Association"]["PublicIp"]


def get_hosted_zone_domain(session: Session, hosted_zone: str) -> str:
    client = session.client("route53")
    response = client.get_hosted_zone(Id=hosted_zone)
    return response["HostedZone"]["Name"]


def update_dns_with_ip(session: Session, hosted_zone: str, fqdn: str, ip: str):
    client = session.client("route53")
    try:
        client.change_resource_record_sets(
            HostedZoneId=hosted_zone,
            ChangeBatch={
                "Changes": [
                    {
                        "Action": "UPSERT",
                        "ResourceRecordSet": {
                            "Name": fqdn,
                            "Type": "A",
                            "TTL": 180,
                            "ResourceRecords": [{"Value": ip}],
                        },
                    }
                ]
            },
        )
    except Exception as err:
        logger.error(err)
