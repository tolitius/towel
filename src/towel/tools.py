import webbrowser, requests
import os, argparse, sys, re, base64, uuid, time
from enum import Enum, auto
from urllib.parse import urlparse
from pathlib import Path
from datetime import datetime

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from pydantic import ValidationError

class LogLevel(Enum):
   INFO = auto()
   DEBUG = auto()
   TRACE = auto()
   WARN = auto()
   ERROR = auto()

class color:
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   GRAY_DARK = '\033[38;5;232m'
   GRAY_ME = '\033[38;5;239m'
   GRAY_DIUM = '\033[38;5;240m'
   GRAY_MEDIUM = '\033[38;5;244m'
   GRAY_LIGHT = '\033[38;5;250m'
   GRAY_VERY_LIGHT = '\033[38;5;254m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'

def say(who,
        message,
        who_color = color.PURPLE,
        message_color = color.GRAY_MEDIUM,
        newline=True):
   print("\n" + color.BLUE + "> " + color.BOLD + who_color + color.UNDERLINE + who + color.END + ": ", end="")
   if newline:
      print(message_color + message + color.END)
   else:
      print(message_color + message + color.END, end="")

def stream(thoughts,
           with_color = color.GRAY_LIGHT,
           who=None,
           who_color = color.PURPLE):

   if who:
      print("\n" + color.BLUE + "> " + color.BOLD + who_color + color.UNDERLINE + who + color.END + ": ", end="")

   idea = ""
   for chunk in thoughts:
      idea += chunk
      print(with_color + f"{chunk}" + color.END, end='', flush=True)

   print("\n")

   return idea

def slurp(source: str) -> str:
    parsed = urlparse(source)

    if parsed.scheme in ['http', 'https']:
        # if slurp from the web
        try:
            response = requests.get(source)
            response.raise_for_status()  # raise for bad responses
            return response.text
        except requests.RequestException as e:
            raise IOError(f"could not read from the URL {source} due to: {e}")
    elif parsed.scheme in ['', 'file'] or Path(source).exists():
        # if slurp from a local file
        try:
            with open(source, 'r') as file:
                return file.read()
        except IOError as e:
            raise IOError(f"could not read file {source} due to: {e}")
    else:
        raise ValueError(f"invalid source: {source}. needs to be a valid local file path or URL")

def name_to_file_name(name, extension="txt"):

    clean_name = re.sub(r'[^a-zA-Z0-9\s-]', '', name).replace(' ', '-').lower()

    timestamp = datetime.now().strftime("%Y-%m-%d.%H-%M-%S-%f")[:-3]
    return f"{clean_name}.{timestamp}.{extension}"

def open_local_browser(dir_path):
   current_dir = os.getcwd()
   try:
      # Get the absolute path of the file
      abs_path = os.path.abspath(dir_path)

      # Check if the file exists
      if os.path.exists(abs_path):
         # Open the file in the default web browser
          webbrowser.open(f"file://{abs_path}/index.html")
          print(f"opened {dir_path} in the web browser")
      else:
         print(f"can't find a file system path to open in the browser: {abs_path}")
   finally:
      os.chdir(current_dir)

def file_to_utf8(path):

   with open(path, "rb") as file:
      image_data = file.read()
      encoded = base64.b64encode(image_data)
      return encoded.decode("utf-8")

def image_path_to_type(path):

    extension = path.split(".")[-1].lower()

    media_types = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "bmp": "image/bmp",
        "tiff": "image/tiff",
        "webp": "image/webp",
        "svg": "image/svg+xml"
    }

    if extension not in media_types:
        raise ValueError(f"could not determine an image type. image path: {path}")

    return media_types[extension]

def image_path_to_data(path):

   return {"image_data": file_to_utf8(path),
           "image_type": image_path_to_type(path)}

def send_post_request(prompt,
                      url="http://localhost:4242/ask"):

    try:
        response = requests.post(url, json = prompt)
        response.raise_for_status()  # raise an exception for 4xx or 5xx status codes

        # process the response
        if response.status_code == 200:
            # print(f"response {response.text}")
            return response.text
        else:
            print(f"request failed with status code: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"an error occurred: {e}")

def squuid():
    "tasty sequential UUIDs: i.e. https://github.com/tolitius/yang/blob/master/src/yang/lang.clj#L25-L36"

    random_uuid = uuid.uuid4()

    current_time_millis = int(time.time() * 1000)
    current_time_bits = (current_time_millis & 0xFFFFFFFF) << 32

    random_msb_lsb = random_uuid.int >> 96 & 0xFFFFFFFF

    new_msb = current_time_bits | random_msb_lsb

    lsb = random_uuid.int & 0xFFFFFFFFFFFFFFFF

    new_uuid_int = (new_msb << 64) | lsb
    squuid = uuid.UUID(int=new_uuid_int)

    return squuid

def check_connection(url,
                     message="failed to connect to server",
                     timeout: int = 10):
    try:
        response = requests.get(f"{url}/api/tags",
                                timeout=timeout)
        response.raise_for_status()

    except requests.RequestException as e:
        raise ConnectionError(f"{message}. tried connecting to: {url} but could not due to {e}")

def warn(message,
         who="thinker"):
    print(color.BLUE + "> " + color.BOLD + color.YELLOW + color.UNDERLINE + who + color.END + ": ", end="")
    print(color.GRAY_DIUM + message + color.END)


## ----------------------------------------------------- retrying instructor calls

def wrap_retry(max_attempts=5,
               wait_multiplier=1,
               wait_min=4,
               wait_max=10,
               retry_exceptions=(ValidationError)):
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=wait_multiplier,
                              min=wait_min,
                              max=wait_max),
        retry=retry_if_exception_type(retry_exceptions),
        reraise=True
    )

def with_retry(iclient,
               instructor_kwargs,
               config=None):

    if config is None:
        config = {}

    @wrap_retry(**config)
    def _with_retry():
        try:
            return iclient.chat.completions.create(**instructor_kwargs)
        except ValidationError as e:
            warn(f"retrying: asking \"{instructor_kwargs['model']}\" to conform the response into \"{instructor_kwargs['response_model'].__name__}\" type")
            raise
        except Exception as e:
            raise

    return _with_retry()
