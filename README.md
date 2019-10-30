# RDS Maintenance
With this script you can check if the Amazon RDS instances of an account have pending maintenance and send a message to the indicated slack channel.

If the maintenance application date is equal to or less than 7 days, you will send the message with a high priority initiator.

[![high-priority.png](https://i.postimg.cc/PxPQXWD7/high-priority.png)](https://postimg.cc/ftQ950B7)

If not, send it with a medium priority indicator.

