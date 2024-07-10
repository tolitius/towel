import argparse, os
from dotenv import load_dotenv

import towel.thinker as thinker
from towel.base import towel, intel, tow
from towel.tools import color, stream
from towel.toolbox.web import search_web

@towel(prompts={'summarize-it': "given this topic: {topic}, and these search results from the web: {results}, focus on the topic and summarize the top 10 most important news items given the topic"})
def read_news(topic):

    llm, prompts, _, feedback, iam = tow()

    results = search_web(topic, results_as="json")

    prompt = prompts['summarize-it'].format(topic=topic,
                                            results=results)
    news = stream(llm.think(prompt=prompt,
                            stream=True),
                  who="news anchor")

    return {'news': news}


# usage:
# $ poetry run python hyperland/news_reader.py -t "latest news on large language models"

def parse_args():
    parser = argparse.ArgumentParser(description="gist the latest news on a given topic")
    parser.add_argument("-t", "--topic", required=True, help="topic to search the news for")

    args = parser.parse_args()
    topic = args.topic

    if topic is None:
        raise ValueError(f"missing the topic to search for news on. please pass it as an argument: -t \"what are the latest news about ...\"")

    return args

def main():

    args = parse_args()

    # llm = thinker.Claude(model="claude-3-haiku-20240307")
    llm = thinker.Ollama(model="llama3:latest")

    print(color.GRAY_MEDIUM + f"{llm}" + color.END)

    with intel(llm=llm):
        news = read_news(args.topic)

if __name__ == '__main__':
    main()
