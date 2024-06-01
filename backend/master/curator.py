import time
from backend.config.config import Config
from backend.context.compression import ContextCompressor
from backend.master.prompts import generate_role_prompt, generate_subquery_role_prompt
from backend.memory.embeddings import Memory
from backend.utils.functions import generate_row, get_retriever, get_sub_queries, scrape_urls, stream_output


class Curator:
    def __init__(
         self,
         query: str, 
         source_urls=None, 
         sources=["WEB"],
         config_path=None, 
         websocket=None,
         visited_urls=set()
     ):
        """
        Initialize the Reach class.
        Args:
            query:
            report_type:
            config_path:
            websocket:
        """
        self.query = query
        self.websocket = websocket
        self.cfg = Config(config_path)
        self.retriever = get_retriever(self.cfg.retriever)
        self.context = []
        self.source_urls = source_urls
        self.sources = sources
        self.memory = Memory(self.cfg.embedding_provider)
        self.visited_urls = visited_urls

    async def conduct_research(self):
            
            self.context = await self.get_context_by_search(self.query)
            # else self.source_urls:
            #     self.context = await self.get_context_by_urls(self.source_urls)

            time.sleep(2)


    async def get_context_by_urls(self, urls):
            """
                Scrapes and compresses the context from the given urls
            """
            new_search_urls = await self.get_new_urls(urls)
            await stream_output("logs",
                                f"I will conduct my research based on the following urls: {new_search_urls}...",
                                self.websocket)
            scraped_sites = scrape_urls(new_search_urls, self.cfg)
            web_results = await self.get_similar_content_by_query(self.query, scraped_sites)

            return web_results

    async def get_context_by_search(self, query):
            """
            Generates the context for the research task by searching the query and scraping the results
            Returns:
                context: List of context
            """
            prompt = generate_subquery_role_prompt()
            sub_queries = await get_sub_queries(query=query, agent_role_prompt=prompt, cfg=self.cfg) + [query]
            await stream_output("logs",
                                f"I will conduct my research based on the following queries: {sub_queries}...",
                                self.websocket)

            # Run Sub-Queries
            for sub_query in sub_queries:
                await stream_output("logs", f"\nRunning research for '{sub_query}'...", self.websocket)
                scraped_sites = await self.scrape_sites_by_query(sub_query)
                web_content = await self.get_similar_content_by_query(sub_query, scraped_sites)

                content = web_content

                if content:
                    await stream_output("logs", f"{content}", self.websocket)
                else:
                    await stream_output("logs", f"No content found for '{sub_query}'...", self.websocket)
            print(f"Collected content: {content}")

            return content

    async def get_new_urls(self, url_set_input):
        """ Gets the new urls from the given url set.
        Args: url_set_input (set[str]): The url set to get the new urls from
        Returns: list[str]: The new urls from the given url set
        """

        new_urls = []
        for url in url_set_input:
            if url not in self.visited_urls:
                await stream_output("logs", f"Adding source url to research: {url}\n", self.websocket)

                self.visited_urls.add(url)
                new_urls.append(url)

        return new_urls

    async def scrape_sites_by_query(self, sub_query):
        """
        Runs a sub-query
        Args:
            sub_query:

        Returns:
            Summary
        """
        # Get Urls
        retriever = self.retriever(sub_query)
        search_results = retriever.search(max_results=self.cfg.max_search_results_per_query)
        new_search_urls = await self.get_new_urls([url.get("href") for url in search_results])

        # Scrape Urls
        await stream_output("logs", f"📝Scraping urls {new_search_urls}...\n", self.websocket)
        # await stream_output("logs", f"Researching for relevant information...\n", self.websocket)
        scraped_content_results = scrape_urls(new_search_urls, self.cfg)
        return scraped_content_results

    async def get_similar_content_by_query(self, query, pages):
        await stream_output("logs", f"Getting relevant content based on query: {query}...", self.websocket)
        # Summarize Raw Data
        print(f"PAGES: {pages}")
        context_compressor = ContextCompressor(documents=pages, embeddings=self.memory.get_embeddings())
        # Run Tasks
        return context_compressor.get_context(query, max_results=8)
    
    async def create_dataset(self):

        dataset = await generate_row(
            query=self.query, 
            context=self.context,
            websocket=self.websocket,
            role_prompt=generate_role_prompt(),
            cfg=self.cfg
        )
        return dataset