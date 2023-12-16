
import datetime
import json
import os
import random
import time
from google.cloud import pubsub_v1

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'YOUR_GCP_CA_PATH'

from google.api_core.exceptions import AlreadyExists
project_id = 'gcp-serverless-workshop' # Google Project Id
topic_id = "workshop-testing-1" # Topic Id
topic_path = f"projects/{project_id}/topics/{topic_id}"
publisher = pubsub_v1.PublisherClient()
msg_list = [{"order_id": 1, "name":"居西批全家優惠碼"},
            {"order_id": 2, "name":"沙發套組"},
            {"order_id": 3, "name":"電燈泡"}]

# 新建一個 Topic
try:
    publisher.create_topic(name=topic_path)
except AlreadyExists:
    print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
          f" [WARNING] Topic \"{topic_id}\" already exists.")

# 定時每 5 秒 Publish 一個隨機 message 到 channel 這個 Topic
while 1:
    message = json.dumps(random.choice(msg_list)).encode()
    publisher.publish(topic_path, message)
    print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [Info] message sent, message: {message}")
    time.sleep(5)
