 import boto3
from datetime import datetime
import time

def delete_log_streams(log_group_name, logs):
    """Delete CloudWatch Logs log streams for a given log group."""
    next_token = None

    while True:
        if next_token:
            log_streams = logs.describe_log_streams(logGroupName=log_group_name, nextToken=next_token)
        else:
            log_streams = logs.describe_log_streams(logGroupName=log_group_name)

        for stream in log_streams['logStreams']:
            log_stream_name = stream['logStreamName']
            print("Delete log stream:", log_stream_name)
            logs.delete_log_stream(logGroupName=log_group_name, logStreamName=log_stream_name)

        next_token = log_streams.get('nextToken')
        if not next_token or len(log_streams['logStreams']) == 0:
            break

def lambda_handler(event, context):
    cloudwatch_logs = boto3.client('logs')
    next_token = None
    log_group_names = []
    start_time = int((time.time() - 7 * 24 * 3600) * 1000)

    while True:
        if next_token:
            log_groups = cloudwatch_logs.describe_log_groups(nextToken=next_token)
        else:
            log_groups = cloudwatch_logs.describe_log_groups()

        for log_group in log_groups['logGroups']:
            log_group_name = log_group['logGroupName']
            log_group_names.append(log_group_name)
            print(log_group_name)
            formatted_date = datetime.utcfromtimestamp(time.time()).strftime('%Y/%m/%d')
            s3_key = f'logs/{formatted_date}/{log_group_name}.log'
            response = cloudwatch_logs.create_export_task(
                logGroupName=log_group_name,
                fromTime=start_time,
                to=int(time.time() * 1000),
                destination='logexportbucket-sagar',
                destinationPrefix=s3_key
            )
            print(response)
            time.sleep(6)
            delete_log_streams(log_group_name, cloudwatch_logs)
        next_token = log_groups.get('nextToken')
        if not next_token:
            break

    return {
        'statusCode': 200,
        'body': {
            'log_group_names': log_group_names,
            'message': 'Export tasks completed, and log streams deleted.'
        }
    }


#EXPORTING SINGLE SPECIFIC LOG TO S3


import boto3
import os
import datetime



GROUP_NAME = "EC2_Test_Log_Instance"
DESTINATION_BUCKET = "logexportbucket-sagar"
PREFIX = "InstanceLogs"
NDAYS = 10
nDays = int(NDAYS)


currentTime = datetime.datetime.now()
StartDate = currentTime - datetime.timedelta(days=nDays)
EndDate = currentTime - datetime.timedelta(days=nDays - 1)


fromDate = int(StartDate.timestamp() * 1000)
toDate = int(EndDate.timestamp() * 1000)

BUCKET_PREFIX = os.path.join(PREFIX, StartDate.strftime('%Y{0}%m{0}%d').format(os.path.sep))


def lambda_handler(event, context):
    client = boto3.client('logs')
    response = client.create_export_task(
         logGroupName=GROUP_NAME,
         fromTime=fromDate,
         to=toDate,
         destination=DESTINATION_BUCKET,
         destinationPrefix=BUCKET_PREFIX
        )
    print(response)
