import time
import pandas as pd
from backend.config.config import Config
from backend.context.compression import ContextCompressor
from backend.master.prompts import generate_role_prompt, generate_subquery_role_prompt
from backend.memory.embeddings import Memory
from backend.utils.functions import generate_row, get_retriever, get_sub_queries, scrape_urls, stream_output, summarize_dataframe
from backend.utils.llm import parse_chat_completion_for_csv

class Curator:
    def __init__(
         self,
         query: str, 
         source_urls, 
         columns, 
         rows, 
         config_path=None, 
         websocket=None,
         visited_urls=set()
     ):
        self.query = query
        self.websocket = websocket
        self.cfg = Config(config_path)
        self.retriever = get_retriever(self.cfg.retriever)
        self.context = []
        self.source_urls = source_urls
        self.columns = columns
        self.rows = rows
        self.existing_data = pd.DataFrame()
        self.memory = Memory(self.cfg.embedding_provider)
        self.visited_urls = visited_urls

    async def conduct_research(self):
        self.context = await self.get_context_by_search(self.query)
        print(f'Found context: {self.context}')
        print(f'curator start cols: {self.columns}')
        # else self.source_urls:
            #     self.context = await self.get_context_by_urls(self.source_urls)

        time.sleep(2)

    async def get_context_by_urls(self, urls):
        new_search_urls = await self.get_new_urls(urls)
        await stream_output("logs", f"I will conduct my research based on the following urls: {new_search_urls}...", self.websocket)
        scraped_sites = scrape_urls(new_search_urls, self.cfg)
        web_results = await self.get_similar_content_by_query(self.query, scraped_sites)
        return web_results

    async def get_context_by_search(self, query):
        prompt = generate_subquery_role_prompt(self.columns)
        sub_queries = await get_sub_queries(query=query, agent_role_prompt=prompt, cfg=self.cfg) + [query]
        await stream_output("logs", f"I will conduct my research based on the following queries: {sub_queries}...", self.websocket)

        content = []
        for sub_query in sub_queries:
            await stream_output("logs", f"\nRunning research for '{sub_query}'...", self.websocket)
            scraped_sites = await self.scrape_sites_by_query(sub_query)
            print(f"scraped sites: {scraped_sites}")
            web_content = await self.get_similar_content_by_query(sub_query, scraped_sites)

            if web_content:
                await stream_output("logs", f"{web_content}", self.websocket)
                content.append(web_content)
            else:
                await stream_output("logs", f"No content found for '{sub_query}'...", self.websocket)
        print(f"Collected content: {content}")

        return content

    async def get_new_urls(self, url_set_input):
        new_urls = []
        for url in url_set_input:
            if url not in self.visited_urls:
                await stream_output("logs", f"Adding source url to research: {url}\n", self.websocket)
                self.visited_urls.add(url)
                new_urls.append(url)
        return new_urls

    async def scrape_sites_by_query(self, sub_query):
        retriever = self.retriever(sub_query)
        search_results = retriever.search(max_results=self.cfg.max_search_results_per_query)
        new_search_urls = await self.get_new_urls([url.get("href") for url in search_results])
        await stream_output("logs", f"📝Scraping urls {new_search_urls}...\n", self.websocket)
        scraped_content_results = scrape_urls(new_search_urls, self.cfg)
        return scraped_content_results

    async def get_similar_content_by_query(self, query, pages):
        await stream_output("logs", f"Getting relevant content based on query: {query}...", self.websocket)
        print(f"PAGES: {pages}")
        context_compressor = ContextCompressor(documents=pages, embeddings=self.memory.get_embeddings())
        return context_compressor.get_context(query, max_results=8)
    
    async def create_rows(self):
        check_len = 0

        while check_len < self.rows:
            if not self.existing_data.empty:
                existing_dataset_str = summarize_dataframe(self.existing_data)
                print(f'Markdown DF: {existing_dataset_str}')
            else:
                existing_dataset_str = "Nothing has been collected yet."
                print("Markdown DF: DataFrame is empty. First pass.")

            print(f'pass in context: {self.context}')

            dataset = await generate_row(
                existing_data=existing_dataset_str,
                context=self.context,
                columns=self.columns,
                websocket=self.websocket,
                role_prompt=generate_role_prompt(),  # existing data
                cfg=self.cfg
            )

            new_data = parse_chat_completion_for_csv(dataset)
            if not new_data.empty:
                if not self.existing_data.empty and not self.existing_data.equals(new_data):
                    print(f'class attr: {self.existing_data}')
                    print(f'new stuff: {new_data}')
                    self.existing_data = pd.concat([self.existing_data, new_data], ignore_index=True)
                elif self.existing_data.empty:
                    print(f'first round stuff: {new_data}')
                    self.existing_data = new_data
            else:
                print("No new data to add.")

            check_len = len(self.existing_data)

        output_dataset = self.existing_data
        return output_dataset