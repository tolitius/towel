import requests
from googlesearch import search as google_search
from duckduckgo_search import DDGS
from bs4 import BeautifulSoup
import re, json
import fitz  # pip install PyMuPDF
from typing import Optional
from towel.tools import say

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



def make_good_search_query(llm,
                           details: str) -> str:
    query_prompt = f"""
    Given the user's details create an effective search query to help them find the information they need.
    The one that would work great for search engines like Google or DuckDuckGo.
    The query should be specific, use relevant keywords, and be formatted for optimal search results.

    user's details: \"{details}\

    provide your search query as a single concise string.

    make sure your search query is clear, relevant, concise, and formatted correctly.
    return no explanation or context, just the search query.
    it needs to be short enough to fit in a search engine's search bar.

    # EXAMPLE 1:
    best Python programming tutorials for beginners 2024

    # EXAMPLE 2:
    latest trends in artificial intelligence 2024

    # EXAMPLE 3:
    health benefits of a plant-based diet research studies

    # EXAMPLE 4:
    comprehensive travel guide Tokyo 2024

    # EXAMPLE 5:
    best practices for remote work productivity tips 2024

    # EXAMPLE 6:
    iPhone 15 detailed reviews and user experiences

    # EXAMPLE 7:
    impacts of climate change on coastal cities 2024

    # EXAMPLE 8:
    effective SEO strategies for small businesses 2024

    # EXAMPLE 9:
    academic papers on machine learning applications in healthcare 2024

    # EXAMPLE 10:
    history and culture of the Renaissance period comprehensive overview
    """
    return llm.think(prompt=query_prompt).content[0].text

def summarize_search_results(llm,
                             search_results: str,
                             context: Optional[str] = None) -> str:
    summarize_prompt = f"""
    Given the following web search results, current context, and the next step's instructions,
    provide a concise summary of the most relevant information. Focus on details that are directly
    applicable to the current problem-solving step.

    web search results: \"{search_results}\"
    context of this search: \"{context}\"

    Summarize the key points as a list in a clear, organized manner.

    # EXAMPLE:

    let's say the context / problem / question is "why LLM limitations are temporary"
    you found a lot of information about the limitations of LLM on the web, and you need to summarize it
    this is what it could look like:


    1. Continuous Improvement in Training Data: As more diverse and comprehensive datasets become
       available, LLMs can be trained on richer data, reducing biases and improving performance across various contexts.

    2. Advancements in Algorithms: Ongoing research in machine learning algorithms is leading
       to more efficient and effective models. Innovations such as more advanced transformers, better
       optimization techniques, and novel architectures will overcome current limitations.

    3. Increased Computational Power: With the rapid advancement of computational hardware, including
       specialized AI processors and quantum computing, LLMs can be trained faster and more effectively,
       allowing for the development of more sophisticated models.

    4. Enhanced Fine-Tuning Techniques: Improved methods for fine-tuning models on specific tasks or
       domains can significantly enhance their accuracy and relevance, addressing current limitations in generalization and adaptability.

    5. Improved Human-AI Collaboration: As interfaces and methodologies for human-AI interaction evolve,
       it becomes easier for humans to guide and correct AI models, making their outputs more reliable and useful.

    6. Development of Hybrid Models: Combining LLMs with other AI technologies, such as symbolic reasoning
       systems or expert systems, can mitigate the weaknesses of each approach, leading to more robust and versatile AI solutions.

    7. Better Understanding of LLMs: As researchers gain a deeper understanding of how LLMs work,
       they can develop better techniques to address issues like hallucinations, lack of context understanding, and other limitations.

    8. Ethical and Regulatory Advances: The establishment of ethical guidelines and regulatory frameworks
       will ensure responsible AI development, encouraging practices that minimize biases and enhance fairness in LLMs.

    9. Community and Open-Source Contributions: The collaborative nature of the AI research community,
       including open-source initiatives, accelerates the identification of problems and the development of solutions,
       leading to rapid advancements in LLM capabilities.

   10. Economic and Societal Demand: As industries and society increasingly rely on AI, there is strong
       economic and societal motivation to overcome LLM limitations, driving investment and innovation in this field.
    """
    return llm.think(prompt=summarize_prompt).content[0].text

def search_and_summarize(llm,
                         search_for,
                         num_results=3):

    search_query = make_good_search_query(llm, search_for)

    say("web search", f"browsing the web for: {search_query}")

    search_results = search_web(search_query,
                                num_results=num_results)

    return summarize_search_results(llm,
                                    search_results,
                                    search_for)
