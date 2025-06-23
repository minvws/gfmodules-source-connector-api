from app.source_connector import SourceConnector


class KvkConnector(SourceConnector):
    """
    Connector for the KVK (Kamer van Koophandel) API.
    """

    def __init__(self, config: dict):
        super().__init__(config)
        self.api_url = config.get("api_url", "https://api.kvk.nl")
        self.api_key = config.get("api_key")

    def connect(self):
        """
        Establish a connection to the KVK API.
        """
        print("Connecting to KVK API at", self.api_url)

    def enrich(self, userinfo: dict) -> dict:
        """
        Fetch data from the KVK API based on the provided userinfo.

        :param userinfo: User information to enrich.
        :return: Enriched data.
        """
        userinfo = self.__parse_userinfo(userinfo)

        data = {
            "company_name": "Example Company",
            "address": "123 Example Street, Example City",
            "status": "Active",
            "registration_date": "2020-01-01",
        }

        userinfo.update(data)

        return userinfo

    def close(self):
        """
        Close the connection to the KVK API.
        """
        print("Closing connection to KVK API")

    def __parse_userinfo(self, userinfo: dict) -> dict:
        """
        Parse the userinfo dictionary to extract relevant fields for KVK API.
        Different login methods result in different userinfo structures,
        so we need to handle various possible keys.

        :param userinfo: User information dictionary.
        :return: Parsed user information.
        """
        possible_keys = [
            "kvk_number",
            "organization_code",
        ]

        for key in possible_keys:
            if key in userinfo and userinfo[key]:
                return {"kvk_number": userinfo[key]}

        raise ValueError("No valid KVK identifier found in userinfo")

