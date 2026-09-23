import json
from typing import Any

from google.cloud import pubsub_v1

from airless.core.hook import QueueHook
from airless.core.utils import get_config


class GooglePubsubHook(QueueHook):
    """Hook for interacting with Google Pub/Sub."""

    def __init__(self) -> None:
        """Initializes the GooglePubsubHook."""
        super().__init__()
        self.publisher = pubsub_v1.PublisherClient()

    def publish(self, project: str, topic: str, data: Any) -> str:
        """Publishes a message to a specified Pub/Sub topic.

        Args:
            project (str): The GCP project ID.
            topic (str): The Pub/Sub topic name.
            data (Any): The data to publish.

        Returns:
            str: A confirmation message.
        """
        if get_config('ENV') == 'prod':
            topic_path = self.publisher.topic_path(
                project or get_config('GCP_PROJECT'), topic
            )

            message_bytes = json.dumps(data, default=str).encode('utf-8')

            publish_future = self.publisher.publish(topic_path, data=message_bytes)
            publish_future.result(
                timeout=int(get_config('PUBSUB_PUBLISH_TIMEOUT', False) or 10)
            )
            self.logger.info(
                f'published to {project or get_config("GCP_PROJECT")}.{topic}'
            )
            return 'Message published.'
        else:
            self.logger.debug(
                f'[DEV] Message published to Project {project or get_config("GCP_PROJECT")}, Topic {topic}: {data}'
            )
