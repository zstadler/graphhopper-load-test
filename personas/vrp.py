import gevent
import json
import locust
import random
import os
import time
from locust import events, TaskSet, task
from locust.contrib.fasthttp import FastHttpUser

from personas import common


class PersonaTaskSet(TaskSet):
    def on_start(self):
        self.client.verify = False
        self.max_profiles = int(os.environ["VRP_MAX_PROFILES"]) if "VRP_MAX_PROFILES" in os.environ else 1
        self.max_locations = int(os.environ["VRP_MAX_LOCATIONS"]) if "VRP_MAX_LOCATIONS" in os.environ else 10
        self.api_key_url_suffix = common.get_api_key_url_suffix("?")

    @task
    def get_vrp(self):

        # set a payload of random locations
        vehicles, vehicle_types = get_random_vehicles_and_types(self.max_profiles)
        data = {
            "vehicles": vehicles,
            "vehicle_types": vehicle_types,
            "services": get_random_services(self.max_locations),
        }
        payload = json.dumps(data)

        # optimize
        url = f"/vrp/optimize{self.api_key_url_suffix}"
        headers = {"content-type": "application/json"}
        with self.client.post(url, catch_response=True, data=payload, headers=headers, name="VRP complex Optimize", timeout=60) as response:
            if response.text is None:
                response.failure("VRP optimize failed, there was no response.")
                return
            try:
                response_data = response.json()
            except json.decoder.JSONDecodeError as e:
                response.failure("VRP optimize failed, json decode error: {}\nCode: {}, Response text: {}".format(e, response.status_code, response.text))
                return
            #except TypeError as e:
            if "job_id" not in response_data:
                response.failure(f"VRP optimize failed, no `job_id` in response. Response: {response_data}")
                return

            job_id = response.json()["job_id"]

        while True:
            url = f"/vrp/solution/{job_id}{self.api_key_url_suffix}"
            with self.client.get(url, catch_response=True, name="VRP complex Solution", timeout=60) as response:
                try:
                    response_data = response.json()
                except (json.decoder.JSONDecodeError, TypeError) as e:
                    response.failure("VRP solution failed, json decode error: {}\nCode: {}, Response text: {}".format(e, response.status_code, response.text))
                    return
                if response.status_code == 400:
                    response.failure("VRP solution failed, HTTP 400. {}".format(response.text))
                    return
                if "status" not in response_data:
                    response.failure("VRP solution failed, no `status` in response.")
                    return
                if response.json()["status"] == "finished":
                    break
                time.sleep(0.33) # maximum 3 GET requests per second


class PersonaVRP(FastHttpUser):
    tasks = [PersonaTaskSet]
    weight = 10
    network_timeout = 3.0
    connection_timeout = 3.0
    wait_time = locust.wait_time.constant_pacing(1.0)


def get_random_vehicles_and_types(max_profiles):
    vehicles = []
    vehicle_types = []
    vrp_tomtom_probability = float(os.environ["VRP_TOMTOM_PROBABILITY"]) if "VRP_TOMTOM_PROBABILITY" in os.environ else 0.2
    for i in range(max_profiles):

        profiles = os.environ["VRP_PROFILES"].split(",") if "VRP_PROFILES" in os.environ else ["hike"]

        vehicle_type = {"type_id": "t{}".format(i), "profile": random.choice(profiles)}
        if random.random() < vrp_tomtom_probability and vehicle_type["profile"] not in [
            "truck",
            "bike",
        ]:  # ensure that your requesting profiles are enabled for tomtom matrix, if not include them here
            vehicle_type["network_data_provider"] = "tomtom"
            vehicle_type["consider_traffic"] = True
        vehicle_types.append(vehicle_type)

        vehicle = {
            "vehicle_id": "vehicle-{}".format(i),
            "type_id": "t{}".format(i),
            "start_address": get_random_location("vehicle-{}".format(i)),
        }
        vehicles.append(vehicle)
    return vehicles, vehicle_types


def get_random_location(name):
    return {
        "location_id": name,
        "lon": random.uniform(13.347702, 13.437996),
        "lat": random.uniform(52.522906, 52.561958),
    }


def get_random_services(max_locations):
    services = []
    for i in range(max_locations):
        services.append(
            {"id": "s{}".format(i), "address": get_random_location("l-{}".format(i))}
        )
    return services
