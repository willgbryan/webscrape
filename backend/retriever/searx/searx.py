
# libraries
import os
from langchain.utilities import SearxSearchWrapper


class SearxSearch():
    """
    Searxng Metasearch Retriever
    """
    def __init__(self, query):
        """
        Initializes the search object
        Args:
            query:
        """
        self.query = query


    def search(self, max_results=7):
        """
        Searches the query
        Returns:

        """
        searx = SearxSearchWrapper(searx_host=os.environ["SEARX_URL"])
        results = searx.results(self.query, max_results)
        # Normalizing results to match the format of the other search APIs
        search_response = [{"href": obj["link"], "body": obj["snippet"]} for obj in results]
        return search_response
