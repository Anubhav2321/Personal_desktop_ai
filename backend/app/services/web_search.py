"""
ARIS Web Search Service
Provides real-time internet search capabilities using DuckDuckGo.
No API key required. Results are returned as text for AI summarization.
"""

from ddgs import DDGS


def search_web(query: str, max_results: int = 5) -> str:
    """
    Search the internet using DuckDuckGo and return text results.
    Returns formatted string with titles, snippets, and URLs.
    """
    try:
        results = DDGS().text(query, max_results=max_results)

        if not results:
            return f"No search results found for '{query}'."

        formatted = f"Web search results for '{query}':\n\n"
        for i, r in enumerate(results, 1):
            title = r.get("title", "No title")
            body = r.get("body", "No description")
            url = r.get("href", "")
            formatted += f"{i}. {title}\n   {body}\n   Source: {url}\n\n"

        return formatted.strip()

    except Exception as e:
        return f"Web search failed: {str(e)}"


def get_web_info(url: str) -> str:
    """
    Fetch the text content of a webpage for the AI to read.
    Returns the first ~3000 chars of visible text from the page.
    """
    try:
        import httpx
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = httpx.get(url, headers=headers, timeout=10, follow_redirects=True)
        response.raise_for_status()

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")

        # Remove script and style elements
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)

        # Clean up whitespace
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        clean_text = "\n".join(lines)

        # Truncate to keep token usage reasonable
        if len(clean_text) > 3000:
            clean_text = clean_text[:3000] + "\n\n... (content truncated)"

        return f"Content from {url}:\n\n{clean_text}"

    except Exception as e:
        return f"Failed to fetch webpage: {str(e)}"


def get_news(topic: str = "technology", max_results: int = 5) -> str:
    """
    Get latest news on a topic using DuckDuckGo News.
    """
    try:
        results = DDGS().news(topic, max_results=max_results)

        if not results:
            return f"No news found for '{topic}'."

        formatted = f"Latest news on '{topic}':\n\n"
        for i, r in enumerate(results, 1):
            title = r.get("title", "No title")
            body = r.get("body", "No description")
            source = r.get("source", "Unknown source")
            date = r.get("date", "")
            formatted += f"{i}. {title}\n   {body}\n   Source: {source} | {date}\n\n"

        return formatted.strip()

    except Exception as e:
        return f"News search failed: {str(e)}"
