import requests
from googlesearch import search as google_search
from duckduckgo_search import DDGS
from bs4 import BeautifulSoup
import re, json
import fitz  # pip install PyMuPDF

def read_url_as_text(url):
    try:
        # fetch the content from the URL
        response = requests.get(url)
        response.raise_for_status()  # check if the request was successful

        # detect content type
        content_type = response.headers.get('Content-Type')

        if 'text/html' in content_type:
            # parse and clean HTML content
            soup = BeautifulSoup(response.content, 'html.parser')

            # remove unwanted tags (script, style, etc.)
            for script in soup(["script", "style"]):
                script.decompose()

            # get the text from the parsed content
            text = soup.get_text()

            # clean up the text by removing extra whitespace and newlines
            cleaned_text = re.sub(r'\s+', ' ', text).strip()

        elif 'application/pdf' in content_type:
            # parse and clean PDF content
            pdf_document = fitz.open(stream=response.content, filetype="pdf")
            text = ""
            for page_num in range(pdf_document.page_count):
                page = pdf_document.load_page(page_num)
                text += page.get_text()

            # clean up the text by removing extra whitespace and newlines
            cleaned_text = re.sub(r'\s+', ' ', text).strip()

        else:
            return f"Unsupported content type: {content_type}"

        return cleaned_text

    except requests.exceptions.RequestException as e:
        return f"Error fetching URL content: {e}"
    except Exception as e:
        return f"Error processing content: {e}"

# usage:
# url = "https://en.wikipedia.org/wiki/Python_(programming_language)"
# cleaned_text = read_url_as_text(url)
# print(cleaned_text)

def web_results_to_json(results):

    results_dict = {f"result-{idx+1}": result['content'] for idx, result in enumerate(results)}

    json_string = json.dumps(results_dict, indent=4)
    return json_string

def search_web(query,
               num_results=5,
               search_engine="google",
               results_as="json"):

    def duckduckgo_search(query, num_results):
        results = DDGS().text(query, max_results=num_results)
        return [result['href'] for result in results]

    def google_search_wrapper(query, num_results):
        return list(google_search(query, num_results=num_results, lang="en"))

    if search_engine.lower() == "google":
        search_results = google_search_wrapper(query, num_results)
    else:
        search_results = duckduckgo_search(query, num_results)

    def get_page_content(url):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # Remove script and style tags
            for script in soup(["script", "style"]):
                script.decompose()

            # Get the text content of the page
            page_text = soup.get_text()

            # Remove extra whitespace and newlines
            page_text = re.sub(r'\s+', ' ', page_text).strip()

            return page_text
        except requests.RequestException as e:
            return f"could not read from url {url}: {str(e)}"

    results = []
    for url in search_results:
        content = get_page_content(url)
        results.append({'url': url, 'content': content[:3500]})

    if results_as.lower() == "json":
        return web_results_to_json(results)

    return results

# usage:
# query = "what are the latest news in LocalLLaMA subreddit?"
# results = search_web(query)
# for idx, result in enumerate(results):
#     print(f"result {idx+1}: {result['url']}")
#     print(result['content'])
#     print('-' * 80)
