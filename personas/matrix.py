import json
import locust
import urllib
from personas import common
from locust import TaskSet, task
from locust.contrib.fasthttp import FastHttpUser


class PersonaTaskSet(TaskSet):

    def on_start(self):
        self.client.verify = False
        self.api_key_url_suffix = common.get_api_key_url_suffix("&")

        # get points information, they need to be lon,lat
        query = common.get_points_query(self)
        points_str = urllib.parse.parse_qs(query)["point"]
        self.points = [[p.split(",")[1], p.split(",")[0]] for p in points_str]

    @task
    def post_matrix(self):
        base_url = "/matrix"
        path = f"{base_url}?{self.api_key_url_suffix}"
        data = {
            "points": self.points,
            "out_arrays": ["times"],
            "profile": "hike"
        }

        with self.client.post(path, catch_response=True, json=data) as response:
            if response.status_code >= 400:
                try:
                    result = response.json()
                except json.decoder.JSONDecodeError:
                    result = {}
                msg = result["message"] if "message" in result else response
                response.failure(msg)


class PersonaMatrix(FastHttpUser):
    tasks = [PersonaTaskSet]
    weight = 1
    network_timeout = 3.0
    connection_timeout = 3.0
    wait_time = locust.wait_time.constant_pacing(1.0)
