from abc import ABC, abstractmethod
from typing import Any, Dict


class SourceConnector(ABC):
    """
    Abstract base class for source connectors.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize the source connector with the given configuration.

        :param config: Configuration dictionary for the source connector.
        """
        self.config = config

    @abstractmethod
    def connect(self) -> None:
        """
        Establish a connection to the source.
        """
        pass

    @abstractmethod
    def enrich(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch data from the source and enrich the given dictionary.

        :param data: Input data to enrich.
        :return: Enriched data.
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """
        Close the connection to the source.
        """
        pass
