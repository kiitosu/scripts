import datetime
import time

import boto3
import pytz


def execute_query(client, log_group, start_time, end_time, query):
    start_query_response = client.start_query(
        logGroupName=log_group,
        startTime=int(start_time.timestamp()),
        endTime=int(end_time.timestamp()),
        queryString=query,
    )
    query_id = start_query_response["queryId"]

    response = None
    while response is None or (
        isinstance(response, dict) and response.get("status") == "Running"
    ):
        print("Waiting for query to complete ...")
        time.sleep(1)
        response = client.get_query_results(queryId=query_id)

    return response


def main():
    client = boto3.client("logs")
    log_group = "/aws/lambda/func-image-etl"

    jst = pytz.timezone("Asia/Tokyo")
    datetime_format = "%Y-%m-%d %H:%M:%S"
    start_time = datetime.datetime.strptime(
        "2022-04-18 00:00:00", datetime_format
    ).replace(tzinfo=jst)
    end_time = datetime.datetime.now(jst)

    # Initial query to find log streams
    LIMIT = 1000
    initial_query = f"""
    fields @logStream ,@timestamp, @message, @log
    | sort @timestamp desc
    | filter @message like /cannot put_object nilebank/ and @message not like /etl-log/
    | limit {LIMIT}
    """
    initial_response = execute_query(
        client, log_group, start_time, end_time, initial_query
    )
    log_streams = set([result[0]["value"] for result in initial_response["results"]])

    print("\n" + "*" * 10)
    print(f"result size is {len(log_streams)}")
    if LIMIT == len(log_streams):
        print("log_streams found maximum number. you may have to increase LIMIT")
    print("*" * 10)

    # Detailed search using logStream list
    logs = []
    ls_count_with_kw = 0
    ls_count_without_kw = 0
    keyword = ".json is already exist."
    for log_stream in log_streams:
        detailed_query = f"""
        fields @timestamp, @message, @logStream, @log
        | sort @timestamp desc
        | filter @message like /{keyword}/
        | filter @logStream = '{log_stream}'
        | limit 1
        """
        detailed_response = execute_query(
            client, log_group, start_time, end_time, detailed_query
        )
        logs.append(detailed_response)
        if len(detailed_response["results"]) == 0:
            print(f"No message found in log stream: {log_stream}")
            ls_count_without_kw += 1
        else:
            print(f"message found in log stream: {log_stream}")
            ls_count_with_kw += 1

    print("\n" + "*" * 10)
    print("Final Results logs")
    print("*" * 10)
    for log in logs:
        print(log)

    print("\n" + "*" * 10)
    print("Final Results counts")
    print("*" * 10)
    print(f"count of logstream contain {keyword} is {ls_count_with_kw}")
    print(f"count of logstream not contain {keyword} is {ls_count_without_kw}")


if __name__ == "__main__":
    main()
