import configparser
import re
import logging
import os
REQUIRED_ENVIRONMENT_VARIABLES = ["SLACK_TOKEN",
                                  "DIGITAL_OCEAN_TOKEN",
                                  "AWS_ACCESS_KEY_ID",
                                  "AWS_SECRET_ACCESS_KEY"]

class Config(object):
    config_file = ".config"
    config = {"slack": {}, "announcements": {}}

    def _normalize_seconds(self, value):
        value = value.lower()

        if re.match("^(\d+)[smhSMH]$", value) is None:
            raise Exception("invalid frequency in: %s" % value)

        if value.endswith("m"):
            value = 60 * int(value[:-1])
        elif value.endswith("h"):
            value = 60 * 60 * int(value[:-1])
        else:
            value = int(value[:-1])
        return value

    def _check_env_variables(self):
        for env_variable in REQUIRED_ENVIRONMENT_VARIABLES:
            if os.getenv(env_variable) is None:
                raise Exception("%s environment variable not set" % (env_variable))
            else:
                self.config[env_variable] = os.getenv(env_variable)

    def read(self):
        config = configparser.ConfigParser()
        config.read('.config')

        slack_shaming_channels = [i.strip() for i in config.get('Slack', 'shaming_channels').split(",")]
        self._check_env_variables()

        self.config["slack"]["shaming_channels"] = slack_shaming_channels
        self.config["announcements"]["ignore_name"] = [i.strip() for i in config.get("Announcements", "ignore_name").split(",")]
        self.config["announcements"]["ignore_earlier_than"] = self._normalize_seconds(config.get("Announcements", "ignore_earlier_than"))

        return self.config
