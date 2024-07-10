import argparse, os
from dotenv import load_dotenv
import json

import towel.thinker as thinker
from towel.base import towel, intel, tow
from towel.tools import color, stream, image_path_to_data
from towel.toolbox.web import search_web

## given an image path:
##   * creates detailed spec for this image
##   * based on this spec builds a standalone ReactJS mockup in a single HTML file

@towel(iam="UX Designer",
        prompts={
    'describe-image': "create detailed requirements for this mockup image so it can be used to convert it to a ReactJS application"})
def see_me(image_path):

    llm, prompts, *_, iam = tow()

    prompt = prompts['describe-image']
    image_data, image_type = image_path_to_data(image_path).values()

    thoughts = stream(llm.think(
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": image_type,
                            "data": image_data,
                            },
                        },
                    {
                        "type": "text",
                        "text": prompt,
                        }
                    ],
                }
            ],
        stream=True),
                      who=iam)

    return thoughts

@towel(iam="Engineer",
        prompts={
            'build-it': """given these requirements: {spec}
                           create a standalone ReactJS mockup in a single HTML file.
                           return the source code only!
                           make sure include vibrant colors, smooth fonts and helpful icons
                           start your response with <!DOCTYPE html>"""
                           })
def create_mockup(spec: str) -> str:

    llm, prompts, *_, iam = tow()
    prompt = prompts['build-it'].format(spec=spec)

    code = stream(llm.think(prompt=prompt,
                            max_tokens=4096,
                            stream=True),
                  who=iam)

    return code

# usage:
# $ poetry run python hyperland/eyes.py -p "path/to/image"

def parse_args():
    parser = argparse.ArgumentParser(description="converts an image to a ReactJS mockup")
    parser.add_argument("-p", "--image-path", required=True, help="path to the image file")

    args = parser.parse_args()
    image_path = args.image_path

    if not os.path.exists(image_path):
        raise FileNotFoundError(f"the path '{image_path}' does not exist")

    if not os.path.isfile(image_path):
        raise OSError(f"the path '{image_path}' is not a file")

    return args

def main():

    args = parse_args()

    llm = thinker.Claude(model="claude-3-haiku-20240307")
    # llm = thinker.Claude(model="claude-3-5-sonnet-20240620")

    print(color.GRAY_MEDIUM + f"{llm}" + color.END)

    with intel(llm=llm):
        spec = see_me(args.image_path)
        create_mockup(spec)

if __name__ == '__main__':
    main()
