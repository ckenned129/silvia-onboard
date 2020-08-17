from awscrt import io, mqtt, auth, http
from awsiot import mqtt_connection_builder
from random import random
import time
import json
import math


class MQTTClient:

    def __init__(self):

        self.constants = json.load(open('config.json', 'r'))['mqtt']

        event_loop_group = io.EventLoopGroup(1)
        host_resolver = io.DefaultHostResolver(event_loop_group)
        client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)
        self.mqtt_connection = mqtt_connection_builder.mtls_from_path(
                    endpoint=self.constants['endpoint'],
                    cert_filepath=self.constants['path_to_cert'],
                    pri_key_filepath=self.constants['path_to_key'],
                    client_bootstrap=client_bootstrap,
                    ca_filepath=self.constants['path_to_root'],
                    client_id=self.constants['client_id'],
                    clean_session=False,
                    keep_alive_secs=6
                    )
        connect_future = self.mqtt_connection.connect()
        connect_future.result()
        print("MQTT Client Connected!")

    def publish(self, message):
        self.mqtt_connection.publish(
            topic=self.constants['topic'],
            payload=json.dumps(message),
            qos=mqtt.QoS.AT_LEAST_ONCE)

    def close(self):
        disconnect_future = self.mqtt_connection.disconnect()
        disconnect_future.result()
        print("MQTT Client Closed!")
