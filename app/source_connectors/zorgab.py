from app.source_connector import SourceConnector


class ZorgABConnector(SourceConnector):
    def __init__(self, config: dict):
        super().__init__(config)
        self.api_url = config.get("api_url", "https://api.zorgab.nl")

    def connect(self):
        print("Connecting to Zorg AB API at", self.api_url)


    def enrich(self, userinfo: dict) -> dict:
        data = {
            "zorg_name": "Example Zorg",
            "zorg_number": "87654321",
            "address": "456 Zorg Street, Zorg City",
            "status": "Active",
            "registration_date": "2021-01-01",
        }

        return data

    def close(self):
        print("Closing connection to Zorg AB API")



