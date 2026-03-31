import random
import locust
from locust import TaskSet, task
from locust.contrib.fasthttp import FastHttpUser

from personas import common


class PersonaTaskSet(TaskSet):
    def on_start(self):
        self.client.verify = False
        self.api_key_url_suffix = common.get_api_key_url_suffix("&")

    @task
    def get_route(self):
        points = ["{:.2f}".format(random.uniform(20.0, 80.0)) for _ in range(4)]
        path = f"/api/1/route?profile=hike&point={points[0]}%2C{points[1]}&point={points[2]}%2C{points[3]}{self.api_key_url_suffix}"
        self.client.get(path, name="Route erratic")


class PersonaRouteInvalid(FastHttpUser):
    tasks = [PersonaTaskSet]
    weight = 1
    network_timeout = 3.0
    connection_timeout = 3.0
    wait_time = locust.wait_time.constant_pacing(1.0)
