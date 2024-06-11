import json
from typing import List
from datetime import datetime, timezone

def generate_search_queries_prompt(question: str,  max_iterations: int=3) -> str:
    """ Generates the search queries prompt for the given question in JSON format.
    Args: 
        question (str): The question to generate the search queries prompt for
        parent_query (str): The main question (only relevant for detailed reports)
        report_type (str): The report type
        uploaded_files (List[str]): List of uploaded files
        max_iterations (int): The maximum number of search queries to generate
    
    Returns: 
        str: The search queries prompt for the given question in JSON format
    """

    prompt = {
        "task": f"Write {max_iterations} google search queries to search online that form an objective opinion from the following task: \"{question}\"",
        "date_needed": f"Use the current date if needed: {datetime.now().strftime('%B %d, %Y')}.",
        "additional_instructions": "Also include in the queries specified task details such as locations, names, etc.",
        "response_format": "You must respond with a list of strings in the following format: [\"query 1\", \"query 2\", \"query 3\"]."
    }

    return json.dumps(prompt, ensure_ascii=False)

def generate_summary_prompt(query, data):
    """ Generates the summary prompt for the given question and text.
    Args: question (str): The question to generate the summary prompt for
            text (str): The text to generate the summary prompt for
    Returns: str: The summary prompt for the given question and text
    """

    return f'{data}\n Using the above text, summarize it based on the following task or query: "{query}".\n If the ' \
           f'query cannot be answered using the text, YOU MUST summarize the text in short.\n Include all factual ' \
           f'information such as numbers, stats, quotes, etc if available. '

def generate_row_prompt(data, columns, existing_data, user_query):
    prompt = (
        f"Presented with a corpus of information: {data}, the user's question: {user_query}, and some already collected data: {existing_data}" \
        f"Your task is to parse the corpus and populate the columns with new information: {columns} as it pertains to the user's question." \
        f"RETURN VALID JSON with column headers: {columns}, populated with appropriate values from the corpus. DO NOT add new column headers." \
        "DO NOT duplicate rows, be cognizant of the already collected data and only add unique rows." \
        "If no appropriate value can be added, add: 'Not found'" \
        "My job depends on you returning valid JSON, please try your best!"
    )
    return prompt
    
def generate_role_prompt():
    return "You are the worlds premier data collection expert that accels in creating balanced, and comprehensive datasets that is only capable of returning .csv outputs."

def generate_subquery_role_prompt(columns):
    return "You are the worlds premier data collection expert that accels in creating balanced, and comprehensive datasets." \
           f"Presented with a user's question and column headers: {columns},"\
           "your task is to come up with topics to search in order to collect a balanced and comprehensive corpus of research to be analyzed."

def fill_empty_value_prompt(data, user_query, row_values, column_header):
    return f"Given the following column header: {column_header}, some other row values from the same row: {row_values}, and the user's goal: {user_query}." \
           f"Your task is to return the appropriate value for the column header provided with the following information: {data}" \
           "ONLY return the row value for the provided column header and nothing else."

def empty_value_prompt(row: str, max_iterations: int=3):
    prompt = {
        "task": f"Write {max_iterations} google search queries to search online that can help fill in missing values for this dataframe row: \"{row}\"",
        "date_needed": f"Use the current date if needed: {datetime.now().strftime('%B %d, %Y')}.",
        "additional_instructions": "Also include in the queries specified task details such as locations, names, etc.",
        "response_format": "You must respond with a list of strings in the following format: [\"query 1\", \"query 2\", \"query 3\"]."
    }

    return json.dumps(prompt, ensure_ascii=False)