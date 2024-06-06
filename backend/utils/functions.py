import asyncio
import json
import os
import numpy as np
import pandas as pd
from colorama import Fore, Style

from backend.master.prompts import generate_row_prompt, generate_search_queries_prompt, generate_summary_prompt
from backend.scraper.scraper import Scraper

from backend.utils.llm import create_chat_completion


async def generate_row(
        existing_data,
        user_query,
        context,
        columns,
        websocket,
        role_prompt,
        cfg,
    ):
        content = (f"{generate_row_prompt(context, columns, existing_data, user_query)}")

        try:
            report = await create_chat_completion(
                model=cfg.smart_llm_model,
                messages=[
                    {"role": "system", "content": f"{role_prompt}"},
                    {"role": "user", "content": content}
                ],
                temperature=0,
                llm_provider=cfg.llm_provider,
                stream=True,
                websocket=websocket,
                max_tokens=cfg.smart_token_limit
            )
        except Exception as e:
            print(f"{Fore.RED}Error in generate_report: {e}{Style.RESET_ALL}")

        return report

async def summarize_dataframe(df, sample_rows=5, sample_columns=20):
    """
    Create a summary of a Pandas DataFrame for ChatGPT.

    Parameters:
        df (Pandas DataFrame): The dataframe to be summarized.
        sample_rows (int): The number of rows to sample
        sample_columns (int): The number of columns to sample

    Returns:
        A markdown string with a summary of the dataframe
    """
    num_rows, num_cols = df.shape

    # Column Summary
    ## Missing value summary for all columns
    # missing_values = pd.DataFrame(df.isnull().sum(), columns=['Missing Values'])
    # missing_values['% Missing'] = missing_values['Missing Values'] / num_rows * 100

    ## Data type summary for all columns
    # column_info = pd.concat([df.dtypes, missing_values], axis=1).reset_index()
    # column_info.columns = ["Column Name", "Data Type", "Missing Values", "% Missing"]
    # column_info['Data Type'] = column_info['Data Type'].astype(str)

    # Basic summary statistics for numerical and categorical columns
    # get basic statistical information for each column
    # numerical_summary = (
    #     df.describe(include=[np.number]).T.reset_index().rename(columns={'index': 'Column Name'})
    # )

    # has_categoricals = any(df.select_dtypes(include=['category', 'datetime', 'timedelta']).columns)

    # if has_categoricals:
    #     categorical_describe = df.describe(include=['category', 'datetime', 'timedelta'])
    #     categorical_summary = categorical_describe.T.reset_index().rename(
    #         columns={'index': 'Column Name'}
    #     )
    # else:
    #     categorical_summary = pd.DataFrame(columns=['Column Name'])

    sample_columns = min(sample_columns, df.shape[1])
    sample_rows = min(sample_rows, df.shape[0])
    sampled = df.sample(sample_columns, axis=1).sample(sample_rows, axis=0)
    columns_df = pd.DataFrame(df.columns, columns=['Column Name'])

    tablefmt = "github"

    # create the markdown string for output
    output = (
        f"## Dataframe Summary\n\n"
        f"Number of Rows: {num_rows:,}\n\n"
        f"Number of Columns: {num_cols:,}\n\n"
        # f"### Column Information\n\n{columns_df.to_markdown(tablefmt=tablefmt)}\n\n"
        f"### Column Information\n\n{columns_df}\n\n"
        # f"### Numerical Summary\n\n{numerical_summary.to_markdown(tablefmt=tablefmt)}\n\n"
        # f"### Categorical Summary\n\n{categorical_summary.to_markdown(tablefmt=tablefmt)}\n\n"
        # f"### Sample Data ({sample_rows}x{sample_columns})\n\n{sampled.to_markdown(tablefmt=tablefmt)}"
         f"### Sample Data ({sample_rows}x{sample_columns})\n\n{sampled}"
    )

    return output


def get_retriever(retriever):
    """
    Gets the retriever
    Args:
        retriever: retriever name

    Returns:
        retriever: Retriever class

    """
    match retriever:
        case "searx":
            from ..retriever import SearxSearch
            retriever = SearxSearch
        case _:
            raise Exception("Retriever not found.")

    return retriever

async def get_sub_queries(query: str, agent_role_prompt: str, cfg, ):
    """
    Gets the sub queries
    Args:
        query: original query
        agent_role_prompt: agent role prompt
        cfg: Config

    Returns:
        sub_queries: List of sub queries

    """
    max_research_iterations = cfg.max_iterations if cfg.max_iterations else 1

    # if os.path.exists("uploads"):
    #     uploaded_files = [f for f in os.listdir("uploads") if os.path.isfile(os.path.join("uploads", f))]
    # else:
    #     uploaded_files = ""
    response = await create_chat_completion(
        model=cfg.smart_llm_model,
        messages=[
            {"role": "system", "content": f"{agent_role_prompt}"},
            {"role": "user", "content": generate_search_queries_prompt(
                query, 
                max_iterations=max_research_iterations
                )
            }
        ],
        temperature=0,
        llm_provider=cfg.llm_provider
    )
    print(f'response: {response}')
    sub_queries = json.loads(response)
    return sub_queries

def scrape_urls(urls, cfg=None):
    """
    Scrapes the urls
    Args:
        urls: List of urls
        cfg: Config (optional)

    Returns:
        text: str

    """
    content = []
    user_agent = cfg.user_agent if cfg else "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0"
    try:
        content = Scraper(urls, user_agent, cfg.scraper).run()
    except Exception as e:
        print(f"{Fore.RED}Error in scrape_urls: {e}{Style.RESET_ALL}")
    return content


async def summarize(query, content, agent_role_prompt, cfg, websocket=None):
    """
    Asynchronously summarizes a list of URLs.

    Args:
        query (str): The search query.
        content (list): List of dictionaries with 'url' and 'raw_content'.
        agent_role_prompt (str): The role prompt for the agent.
        cfg (object): Configuration object.

    Returns:
        list: A list of dictionaries with 'url' and 'summary'.
    """

    # Function to handle each summarization task for a chunk
    async def handle_task(url, chunk):
        summary = await summarize_url(query, chunk, agent_role_prompt, cfg)
        if summary:
            await stream_output("logs", f"Summarizing url: {url}", websocket)
            await stream_output("logs", f"{summary}", websocket)
        return url, summary

    # Function to split raw content into chunks of 10,000 words
    def chunk_content(raw_content, chunk_size=10000):
        words = raw_content.split()
        for i in range(0, len(words), chunk_size):
            yield ' '.join(words[i:i+chunk_size])

    # Process each item one by one, but process chunks in parallel
    concatenated_summaries = []
    for item in content:
        url = item['url']
        raw_content = item['raw_content']

        # Create tasks for all chunks of the current URL
        chunk_tasks = [handle_task(url, chunk) for chunk in chunk_content(raw_content)]

        # Run chunk tasks concurrently
        chunk_summaries = await asyncio.gather(*chunk_tasks)

        # Aggregate and concatenate summaries for the current URL
        summaries = [summary for _, summary in chunk_summaries if summary]
        concatenated_summary = ' '.join(summaries)
        concatenated_summaries.append({'url': url, 'summary': concatenated_summary})

    return concatenated_summaries


async def summarize_url(query, raw_data, agent_role_prompt, cfg):
    """
    Summarizes the text
    Args:
        query:
        raw_data:
        agent_role_prompt:
        cfg:

    Returns:
        summary: str

    """
    summary = ""
    try:
        summary = await create_chat_completion(
            model=cfg.fast_llm_model,
            messages=[
                {"role": "system", "content": f"{agent_role_prompt}"},
                {"role": "user", "content": f"{generate_summary_prompt(query, raw_data)}"}],
            temperature=0,
            llm_provider=cfg.llm_provider
        )
    except Exception as e:
        print(f"{Fore.RED}Error in summarize: {e}{Style.RESET_ALL}")
    return summary

async def stream_output(type, output, websocket=None, logging=True):
    """
    Streams output to the websocket
    Args:
        type:
        output:

    Returns:
        None
    """
    if not websocket or logging:
        print(output)

    if websocket:
        await websocket.send_json({"type": type, "output": output})