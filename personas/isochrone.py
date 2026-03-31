from personas import common

import locust
from locust import TaskSet, task
from locust.contrib.fasthttp import FastHttpUser


class PersonaTaskSet(TaskSet):
    def on_start(self):
        self.client.verify = False
        self.api_key_url_suffix = common.get_api_key_url_suffix("&")

    @task
    def get_isochrone(self):
        points = ",".join(str(p) for p in common.get_random_berlin_point())
        path = f"/api/1/isochrone?profile=hike&point={points}{self.api_key_url_suffix}"
        self.client.get(path, name="Isochrone")


class PersonaIsochrone(FastHttpUser):
    tasks = [PersonaTaskSet]
    weight = 1
    network_timeout = 3.0
    connection_timeout = 3.0
    wait_time = locust.wait_time.constant_pacing(1.0)
