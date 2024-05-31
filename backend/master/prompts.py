import json
from typing import List
from datetime import datetime, timezone

def generate_search_queries_prompt(question: str, parent_query: str, report_type: str, uploaded_files: List[str], max_iterations: int=3) -> str:
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
        "task": f"Write {max_iterations} google search queries to search online that form an objective opinion from the following task: \"{task}\"",
        "date_needed": f"Use the current date if needed: {datetime.now().strftime('%B %d, %Y')}.",
        "files_info": f"Files can be present and questions can be asked about them. Uploaded files if any: {uploaded_files}",
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

def generate_row_prompt(query, data):
    return f"Task: Analyze the provided data: {data}, and return information relevant to the users question: {query}"

def generate_role_prompt():
    return "You are the worlds premier data collection expert that accels in creating balanced, and comprehensive datasets." \
           "Presented with a corpus of information and existing collected data, your goal is to parse the corpus to add to the collected data."