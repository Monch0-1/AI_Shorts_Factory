# CreateShorts/Data_Context_Service/ContextualDataService.py
import json
from google import genai
from google.genai import types
import os
from googleapiclient.discovery import build  # Example for Google Search API
from typing import List

# Assume load_env_data provides necessary API keys and IDs
from ..Create_Short_Service.loadEnvData import load_env_data, load_unified_assets

api_assets = load_unified_assets()
SEARCH_API_KEY = api_assets.get("SEARCH_API_KEY")
SEARCH_ENGINE_ID = api_assets.get("SEARCH_ENGINE_ID")
client = api_assets.get("GEMINI_CLIENT")



# Note: The actual Google Search API library (google-api-python-client)
# must be installed for perform_google_search to work in production.

def perform_google_search(query: str) -> List[str]:
    """
    Performs a Google Custom Search and returns a list of relevant snippets.

    Args:
        query (str): The search term (e.g., "Genshin meta supports").
        api_key (str): Your Google API Key.
        cx (str): Your Search Engine ID.

    Returns:
        List[str]: A list of strings containing the titles and snippets of the results.
    """
    try:
        # 1. Build the search service
        service = build(
            "customsearch",
            "v1",
            developerKey=api_assets.get("SEARCH_API_KEY")
        )

        # 2. Execute the search
        # num=5 requests 5 results; cx is your search engine ID
        result = service.cse().list(
            q=query,
            cx=api_assets.get("SEARCH_ENGINE_ID"),
            num=5
        ).execute()

        # 3. Extract and format the data (the snippet and title are the context)
        context_list = []

        for item in result.get('items', []):
            title = item.get('title', '')
            snippet = item.get('snippet', '')

            # Format: Title: [Title] | Snippet: [Description]
            # This gives Gemini context to know the source and content.
            context_list.append(f"Title: {title} | Snippet: {snippet}")

        return context_list

    except Exception as e:
        print(f"ERROR performing Google Search for query '{query}': {e}")
        return []


def get_fresh_context(topic: str) -> str:
    """
    Fetches real-time data using Google Search and uses Gemini Flash to distill
    the most critical information into a concise context paragraph.
    """

    # Load environment data and initialize clients
    # env_data = load_env_data()
    # client = env_data.get('GEMINI_CLIENT')
    # SEARCH_API_KEY = env_data.get('GOOGLE_SEARCH_API_KEY')
    # SEARCH_ENGINE_ID = env_data.get('GOOGLE_SEARCH_ENGINE_ID')


    if not SEARCH_API_KEY or not SEARCH_ENGINE_ID:
        # Fallback if keys are missing
        return f"FALLBACK: Search API keys not configured. Cannot fetch fresh data for '{topic}'."

    # 1. Execute Targeted Web Search
    search_queries = [
        f"Best current meta analysis {topic}",
        f"Tier list {topic}"
    ]

    all_snippets = []
    for q in search_queries:
        # NOTE: You would replace this with the real Google API call.
        snippets = perform_google_search(q)
        all_snippets.extend(snippets)

    if not all_snippets:
        return ""

    snippets_str = "\n".join(f"- {s}" for s in all_snippets)

    # 2. Distillation Instruction (Using Gemini Flash for Speed)
    distillation_prompt = f"""
    You are an expert data analyst. Condense the following web search information
    into a concise paragraph (3 to 4 sentences max) that highlights the most CRITICAL and CURRENT points for the user's requested topic.

    Requested Topic: {topic}

    Web Information Obtained:
    ---
    {snippets_str}
    ---

    OUTPUT: Return ONLY the concise context paragraph.
    """

    try:
        # Use the client for the distillation task
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=distillation_prompt,
            config=types.GenerateContentConfig(temperature=0.1)  # Low temperature for factual precision
        )
        return response.text.strip()

    except Exception as e:
        print(f"Error distilling context with Gemini Flash: {e}")
        return f"FALLBACK: Failed to distill context for '{topic}'."
