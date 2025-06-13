from abc import ABC, abstractmethod

class SourceConnector(ABC):
    """
    Abstract base class for source connectors.
    """

    def __init__(self, config: dict):
        """
        Initialize the source connector with the given configuration.

        :param config: Configuration dictionary for the source connector.
        """
        self.config = config

    @abstractmethod
    def connect(self):
        """
        Establish a connection to the source.
        """
        pass

    @abstractmethod
    def enrich(self):
        """
        Fetch data from the source.
        """
        pass

    @abstractmethod
    def close(self):
        """
        Close the connection to the source.
        """
        pass
