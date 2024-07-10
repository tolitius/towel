import argparse, os
from dotenv import load_dotenv

from towel import thinker, towel, intel, tow
from towel.tools import color, stream
from towel.toolbox.web import read_url_as_text


@towel(prompts={'main points': 'summarize the main points in this paper',
                'eli5':        'explain this paper like I\'m 5 years old',
                'issues':      'summarize issues that you can identify with ideas in this paper'})
def summarize_paper(url):

    llm, prompts, *_ = tow()

    paper = read_url_as_text(url)

    ## extract the main points
    summary = stream(llm.think(prompt=prompts['main points'] + paper,
                               stream=True),
                     who="main points")

    ## explain the paper like I'm 5
    eli5 = stream(llm.think(prompt=prompts['eli5'] + paper,
                            stream=True),
                  who="eli5")

    ## identify issues with this paper
    issues = stream(llm.think(prompt=prompts['issues'] + paper,
                              stream=True),
                    who="issues")

    return {'main points': summary,
            'eli5':        eli5,
            'issues':      issues}


# usage:
# $ poetry run python hyperland/paper_summarizer.py -p "https://url/to/whitepaper"

def parse_args():
    parser = argparse.ArgumentParser(description="summarizes a white paper from a given URL")
    parser.add_argument("-p", "--paper-url", help="white paper url")

    args = parser.parse_args()
    paper_url = args.paper_url

    if paper_url is None:
        ## "The Era of 1-bit LLMs: All Large Language Models are in 1.58 Bits"
        args.paper_url = "https://arxiv.org/pdf/2402.17764"

    return args

def main():

    args = parse_args()

    # llm = thinker.Claude(model="claude-3-haiku-20240307")
    llm = thinker.Ollama(model="llama3:latest")
    print(color.GRAY_MEDIUM + f"{llm}" + color.END)

    with intel(llm=llm):
        summary = summarize_paper(args.paper_url)

    # print(color.GRAY_MEDIUM + f"paper summary: {summary}" + color.END)

if __name__ == '__main__':
    main()
