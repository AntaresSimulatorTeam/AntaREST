import time
from locust import HttpUser, task, between, SequentialTaskSet


class AdminUser(HttpUser):
    wait_time = between(1, 2.5)

    @task
    def get_studies(self):
        res = self.client.get("/studies")
        studies = res.json()
        for study_id in studies:
            self.client.get(f"/studies/{study_id}", params={"depth": -1})
            time.sleep(0.2)

    def on_start(self):
        res = self.client.post(
            "/login", data={"username": "admin", "password": "admin"}
        )
        credentials = res.json()
        self.client.headers.update(
            {"Authorization": f'Bearer {credentials["access_token"]}'}
        )
