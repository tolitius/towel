import json
from towel import thinker, towel, tow, intel

def convert_json_to_markdown(article: str) -> str:

    parsed = json.loads(article)
    md = []
    md.append(f"# {parsed.get('title', 'Untitled')}")
    md.append(f"By {parsed.get('author', 'Unknown Author')}\n")

    for section in parsed.get('sections', []):
        md.append(f"## {section.get('title', 'Untitled Section')}")
        md.append(section.get('content', ''))
        md.extend(f"- {item}" for item in section.get('list', []))
        md.extend(f"[{link['text']}]({link['url']})" for link in section.get('links', []))
        md.append('')
    md.append(f"## Conclusion\n{parsed.get('conclusion', 'No conclusion provided.')}")

    return '\n'.join(md)

json_article = """
    {
        "title": "The Art of Programming",
        "author": "Jane Coder",
        "sections": [
            {
                "title": "Introduction",
                "content": "Programming is both a science and an art."
            },
            {
                "title": "Key Concepts",
                "list": [
                    "**Algorithms**: Step-by-step procedures",
                    "**Data Structures**: Organizing data",
                    "**Abstraction**: Simplifying complex systems"
                ]
            },
            {
                "title": "Learning Resources",
                "links": [
                    {"text": "Codecademy", "url": "https://www.codecademy.com/"},
                    {"text": "freeCodeCamp", "url": "https://www.freecodecamp.org/"}
                ]
            }
        ],
        "conclusion": "Start coding today!"
    }
    """

## --------------------------- make it warm

@towel(prompts={"to_markdown": "convert this JSON {article} to markdown"})
def json_to_markdown(article: str) -> str:

  llm, prompts, *_ = tow()
  thought = llm.think(prompts['to_markdown'].format(article=article))

  return thought.content[0].text

def main():

    print("python function (cold):\n")
    print(convert_json_to_markdown(json_article))

    llm = thinker.Ollama(model="llama3:latest")

    with intel(llm=llm):
        markdown = json_to_markdown(json_article)

    print("python function (warm):\n")
    print(markdown)

if __name__ == "__main__":
    main()
