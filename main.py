import digitalocean
from slacker import Slacker
import time
import humanize
import os
import boto
import datetime
from config import Config
import logging
import sys
import re

c = Config()
try:
    configdata = c.read()
except Exception as e:
    logging.critical(e)
    sys.exit(1)


def aws_instances():
    running_instances = []
    conn = boto.connect_ec2(configdata["AWS_ACCESS_KEY_ID"],
                            configdata["AWS_SECRET_ACCESS_KEY"])

    for region in conn.get_all_regions():
        conn = region.connect()

        instances = conn.get_only_instances()

        for instance in instances:
            if instance._state.name == "running":
                running_instances.append(instance)
    return running_instances


def do_instances():
    running_instances = []
    for droplet in do_manager.get_all_droplets():
        running_instances.append(droplet)

    return running_instances

slacker_manager = Slacker(os.getenv("SLACK_TOKEN"))
do_manager = digitalocean.Manager(token=os.getenv("DIGITAL_OCEAN_TOKEN"))

entries = []
ignore_count = 0

for i in aws_instances():
    running_since = datetime.datetime.strptime(i.launch_time,'%Y-%m-%dT%H:%M:%S.%fZ')
    entries.append("AWS - %s (tags: %s), instance_type=%s" % (i.id, i.tags, i.instance_type))

for i in do_instances():
    droplet_created = datetime.datetime.strptime(i.created_at,'%Y-%m-%dT%H:%M:%SZ')

    if configdata.get("announcements").get("ignore_earlier_than"):
        ignore_earlier_than = configdata.get("announcements").get("ignore_earlier_than")
        if int(time.time() - droplet_created.timestamp()) <= ignore_earlier_than:
            logging.critical("ignoring %s since it was created earlier than %d seconds ago" % (i.name, ignore_earlier_than))
            ignore_count+=1
            continue

    if configdata.get("announcements").get("ignore_name"):
        ignore = False
        for ignore_regex in configdata.get("announcements").get("ignore_name"):
            if re.match(ignore_regex, i.name):
                logging.critical("ignoring %s since it matches %s", i.name, ignore_regex)
                ignore_count+=1
                ignore = True
    if not ignore:
        entries.append("DO - %s (tags: %s), created %s ago" % (i.name, i.tags, humanize.naturaldelta(droplet_created)))
entries.append("DO - ignored instances: %d" % (ignore_count))

for channel in configdata.get("slack").get("shaming_channels"):
    slacker_manager.chat.post_message(channel, "\n".join(entries))
