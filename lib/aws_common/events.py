import re

from aws_cdk import aws_events as events
from cron_converter import Cron


def convert_schedule_to_cron(schedule: events.Schedule) -> Cron:
    expr = schedule.expression_string
    expr = expr.replace("?", "*")
    m = re.search(r"\((.*)\)", expr)
    if m:
        val = m.group(1)[:-2]
        return Cron(val)
    return None
