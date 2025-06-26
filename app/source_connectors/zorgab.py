import logging
from typing import Any, Dict

import requests

from app.source_connector import SourceConnector

logger = logging.getLogger(__name__)


class ZorgABConnector(SourceConnector):
    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config)
        self.api_url: str = config.get("api_url", "")
        self.mtls_cert: str = config.get("mtls_cert", "")
        self.mtls_key: str = config.get("mtls_key", "")
        self.mtls_ca: str = config.get("mtls_ca", "")

    def connect(self) -> None:
        logger.info("Connecting to Zorg AB API at", self.api_url)

    def enrich(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.api_url:
            raise ValueError("API URL is not configured")
        if not self.mtls_cert or not self.mtls_key or not self.mtls_ca:
            raise ValueError("mTLS certificates are not configured")

        try:
            response = requests.post(
                self.api_url + "/Organization/_search",
                params={"identifier": data["organization_code"]},
                headers={
                    "Content-Type": "application/json+fhir",
                    "Accept": "application/json+fhir",
                },
                cert=(self.mtls_cert, self.mtls_key),
                verify=self.mtls_ca,
            )

            bundle = response.json()

            if "resourceType" not in bundle or "entry" not in bundle:
                logger.warning("No valid bundle found in response")
                return data

            if bundle["resourceType"] != "Bundle":
                logger.warning("Response is not a valid Bundle resource")
                return data

            if len(bundle["entry"]) == 0:
                logger.warning("No entries found in the bundle")
                return data

            entry = bundle["entry"][0]
            data["organization_name"] = entry["resource"]["name"]

            if "address" in entry["resource"] and entry["resource"]["address"]:
                addr = entry["resource"]["address"][0]
                data["organization_address"] = {
                    "street": ",".join(addr["line"]) if "line" in addr else "",
                    "postalCode": addr.get("postalCode", ""),
                    "city": addr.get("city", ""),
                    "state": addr.get("state", ""),
                    "country": addr.get("country", ""),
                }

        except Exception as e:
            logger.error(f"Error connecting to Zorg AB API: {e}")
            raise

        return data

    def close(self) -> None:
        logger.info("Closing connection to Zorg AB API")
