from personas import common

import locust
from locust import TaskSet, task
from locust.contrib.fasthttp import FastHttpUser


class PersonaTaskSet(TaskSet):

    def on_start(self):
        self.client.verify = False
        self.api_key_url_suffix = common.get_api_key_url_suffix("&")
        self.points_query = common.get_points_query(self)

    @task
    def get_route(self):
        base_url = "/route"
        path = f"{base_url}?profile=hike&{self.points_query}{self.api_key_url_suffix}"
        self.client.get(path, name="Route")


class PersonaRoute(FastHttpUser):
    tasks = [PersonaTaskSet]
    weight = 1
    network_timeout = 3.0
    connection_timeout = 3.0
    wait_time = locust.wait_time.constant_pacing(1.0)
