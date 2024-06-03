import asyncio
import time
import pandas as pd
from backend.config.config import Config
from backend.context.compression import ContextCompressor
from backend.master.prompts import generate_role_prompt, generate_subquery_role_prompt, fill_empty_value_prompt, empty_value_prompt
from backend.memory.embeddings import Memory
from backend.utils.functions import generate_row, get_retriever, get_sub_queries, scrape_urls, stream_output, summarize_dataframe
from backend.utils.llm import create_chat_completion, parse_chat_completion_for_csv

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
        # check_len = 0
        # iter = 1

        # while check_len < self.rows:
        if not self.existing_data.empty:
            existing_dataset_str = await summarize_dataframe(self.existing_data)
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

        # print(f'pass {iter}: {dataset}')

        new_data = await parse_chat_completion_for_csv(dataset)
        await asyncio.sleep(0)  # Ensures new_data is fully instantiated before proceeding
            # new_data.reset_index(drop=True, inplace=True)
            
            # print(f'Existing data:\n{self.existing_data}')
            # print(f'New data:\n{new_data}')
            # print(f"Type of existing_data: {type(self.existing_data)}, columns: {self.existing_data.columns}")
            # print(f"Type of new_data: {type(new_data)}, columns: {new_data.columns}")

            # if new_data.empty:
            #     print("New data is empty, skipping this iteration.")
            #     continue

            # if self.existing_data.columns.size == 0:
            #     print("Existing data is empty, initializing with new data columns.")
            #     self.existing_data = pd.DataFrame(columns=new_data.columns)
            #     print(f'Initialized existing data columns: {self.existing_data.columns}')

            # if set(self.existing_data.columns) != set(new_data.columns):
            #     print(f"Column mismatch between existing and new data. Existing columns: {self.existing_data.columns}, New columns: {new_data.columns}")
            #     raise ValueError("Column mismatch between existing and new data frames")

            # self.existing_data = pd.concat([self.existing_data, new_data]).drop_duplicates().reset_index(drop=True)
            # check_len = len(self.existing_data)
            # print(f'Updated existing data:\n{self.existing_data}')

        output_dataset = new_data
        return output_dataset

    
    async def fill_empty_rows(self, dataset: pd.DataFrame) -> pd.DataFrame:
        final_dataset = dataset.copy()
        for index, row in dataset.iterrows():
            for column in dataset.columns:
                print(f'column iter: {column}')
                if pd.isnull(row[column]) or row[column] == '':

                    prompt = empty_value_prompt(row)
                    new_context = await self.get_context_by_search(prompt)
                    role_prompt = generate_role_prompt()
                    generate_value_prompt = fill_empty_value_prompt(new_context, self.query, row, column)

                    value = await create_chat_completion(
                            model=self.cfg.smart_llm_model,
                            messages=[
                                {"role": "system", "content": f"{role_prompt}"},
                                {"role": "user", "content": generate_value_prompt}
                            ],
                            temperature=0,
                            llm_provider=self.cfg.llm_provider,
                            stream=True,
                            websocket=self.websocket,
                            max_tokens=self.cfg.smart_token_limit
                        )
                    print(f'generated value: {value}')

                    if value:
                        final_dataset.at[index, column] = value

                    print(f'Updated dataset at {[index, column]} with {value}')

        return final_dataset

