#!/usr/bin/env python
from datetime import datetime

import boto3
import slack


class RdsMaintenance(object):
    """
    A class used to verify that Amazon RDS instances have pending maintenance
    and send the result to an indicated slack channel.

    ...

    Attributes
    ----------
    slack_token : str
        Token to authenticate with slack API.

    slack_channel : str
        Slack channel to which messages are sent.

    instance_name : str
        RDS instance name

    mnt_alerts : list
        Two-dimensional list containing maintenance information.

    Methods
    -------
    do_check_mnt()
    Search all RDS instances if there are pending maintenance.

    instance_is_writer(instance_name)
    Check if the last instance name has the role of writer in the cluster.

    send_to_slack(mnt_alerts)
    For each instance that has a maintenance pending send a pre-formatted message to the indicated slack channel.

    """

    def __init__(self, slack_token, slack_channel):
        """
        Parameters
        ----------
        :param slack_token: str
            Token to authenticate with slack API.

        :param slack_channel: str
            Slack channel to which messages are sent.

        rds : object
            Instance boto3.client

        :return: Call do_check_mnt method.
        """
        self.slack_token = slack_token
        self.slack_channel = slack_channel
        #TODO More Auth types for AWS
        self.rds = boto3.client('rds')
        self.do_check_mnt()

    def do_check_mnt(self):
        """
        Search all RDS instances if there are pending maintenance.

        :return: Call send_to_slack(mnt_alerts)
        """
        try:
            mnt_alerts = []
            rds_instances = self.rds.describe_db_instances()
            for instance in rds_instances['DBInstances']:
                instances_pending_mnt = self.rds.describe_pending_maintenance_actions(
                    ResourceIdentifier=instance['DBInstanceArn']
                )
                if instances_pending_mnt['PendingMaintenanceActions']:
                    for instance_pending_mnt in instances_pending_mnt['PendingMaintenanceActions']:
                        ins = (instance_pending_mnt['ResourceIdentifier'].split(":"))[6]
                        for mnt_info in instance_pending_mnt['PendingMaintenanceActionDetails']:
                            days2mnt = datetime.strptime(mnt_info['CurrentApplyDate'].strftime("%m-%d-%y"), '%m-%d-%y')\
                                       - datetime.strptime(datetime.now().strftime("%m-%d-%y"), '%m-%d-%y')
                            data = [
                                ins,
                                mnt_info['Action'],
                                str(self.instance_is_writer(ins)),
                                mnt_info['CurrentApplyDate'].strftime("%b %d %Y %H:%M:%S"),
                                mnt_info['Description'],
                                days2mnt
                            ]
                            mnt_alerts.append(data)
            self.send_to_slack(mnt_alerts)
        except Exception as error:
            print(error)

    def instance_is_writer(self, instance_name):
        """
        Check if the last instance name has the role of writer in the cluster.

        :param instance_name: str
            RDS instance name

        :return: bolean
        """
        instances = self.rds.describe_db_instances(DBInstanceIdentifier=instance_name)
        for instance in instances['DBInstances']:
            cluster_name = instance['DBClusterIdentifier']
            clusters = self.rds.describe_db_clusters(DBClusterIdentifier=cluster_name)
            for cluster in clusters['DBClusters']:
                for cluster_info in cluster['DBClusterMembers']:
                    if cluster_info['DBInstanceIdentifier'] == instance_name:
                        if cluster_info['IsClusterWriter'] is True:
                            return True
                        else:
                            return False
                    else:
                        return False

    def send_to_slack(self, mnt_alerts):
        """
        For each instance that has a maintenance pending send a pre-formatted message to the indicated slack channel.

        :param mnt_alerts: list
            Two-dimensional list containing maintenance information.

        """
        client = slack.WebClient(token=self.slack_token)
        for mnt in mnt_alerts:
            if mnt[5].days <= 7:
                img_url = "https://api.slack.com/img/blocks/bkb_template_images/highpriority.png"
                priority = "High Priority"
            else:
                img_url = "https://api.slack.com/img/blocks/bkb_template_images/mediumpriority.png"
                priority = "Medium Priority"
            msg = [
                {
                    "type": "divider"
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "image",
                            "image_url": img_url,
                            "alt_text": priority
                        },
                        {
                            "type": "mrkdwn",
                            "text": "*" + priority + "*"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "`" + mnt[0] + "`"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": "*Action:*\n" + mnt[1] + ""
                        },
                        {
                            "type": "mrkdwn",
                            "text": "*IsWriter:*\n" + str(mnt[2]) + ""
                        },
                        {
                            "type": "mrkdwn",
                            "text": "*ForcedApplyDate:*\n" + mnt[3] + ""
                        },
                        {
                            "type": "mrkdwn",
                            "text": "*Description:*\n" + mnt[4] + ""
                        }
                    ]
                },
                {
                    "type": "divider"
                }
            ]
            client.chat_postMessage(
                channel=self.slack_channel,
                blocks=msg
            )


if __name__ == "__main__":
    slack_token = '<SLACK TOKEN>'
    slack_channel = "<SLACK CHANNEL>>"
    RdsMaintenance(slack_token, slack_channel)
