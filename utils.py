import datetime

def timestamp_to_date(timestamp):
    timestamp = timestamp - 3600
    if timestamp < 0:
        timestamp = 3600 + timestamp
    return datetime.datetime.fromtimestamp(timestamp).strftime('%H:%M:%S')