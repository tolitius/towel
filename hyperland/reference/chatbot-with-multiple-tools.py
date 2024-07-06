# reference implementation of https://github.com/anthropics/courses/blob/master/ToolUse/06_chatbot_with_multiple_tools.ipynb
# w/ towel

import json
from typing import List, Dict, Union, Any
from pydantic import BaseModel
from towel.base import towel, tow
from towel.tools import color, LogLevel, stream, say, slurp
from towel.brain.base import TextThought, ToolUseThought
import towel.thinker as thinker

class FakeDatabase:
    def __init__(self):
        self.customers = [
            {"id": "1213210", "name": "John Doe", "email": "john@gmail.com", "phone": "123-456-7890", "username": "johndoe"},
            {"id": "2837622", "name": "Priya Patel", "email": "priya@candy.com", "phone": "987-654-3210", "username": "priya123"},
            {"id": "3924156", "name": "Liam Nguyen", "email": "lnguyen@yahoo.com", "phone": "555-123-4567", "username": "liamn"},
            {"id": "4782901", "name": "Aaliyah Davis", "email": "aaliyahd@hotmail.com", "phone": "111-222-3333", "username": "adavis"},
            {"id": "5190753", "name": "Hiroshi Nakamura", "email": "hiroshi@gmail.com", "phone": "444-555-6666", "username": "hiroshin"},
            {"id": "6824095", "name": "Fatima Ahmed", "email": "fatimaa@outlook.com", "phone": "777-888-9999", "username": "fatimaahmed"},
            {"id": "7135680", "name": "Alejandro Rodriguez", "email": "arodriguez@protonmail.com", "phone": "222-333-4444", "username": "alexr"},
            {"id": "8259147", "name": "Megan Anderson", "email": "megana@gmail.com", "phone": "666-777-8888", "username": "manderson"},
            {"id": "9603481", "name": "Kwame Osei", "email": "kwameo@yahoo.com", "phone": "999-000-1111", "username": "kwameo"},
            {"id": "1057426", "name": "Mei Lin", "email": "meilin@gmail.com", "phone": "333-444-5555", "username": "mlin"}
        ]

        self.orders = [
            {"id": "24601", "customer_id": "1213210", "product": "Wireless Headphones", "quantity": 1, "price": 79.99, "status": "Shipped"},
            {"id": "13579", "customer_id": "1213210", "product": "Smartphone Case", "quantity": 2, "price": 19.99, "status": "Processing"},
            {"id": "97531", "customer_id": "2837622", "product": "Bluetooth Speaker", "quantity": 1, "price": "49.99", "status": "Shipped"},
            {"id": "86420", "customer_id": "3924156", "product": "Fitness Tracker", "quantity": 1, "price": 129.99, "status": "Delivered"},
            {"id": "54321", "customer_id": "4782901", "product": "Laptop Sleeve", "quantity": 3, "price": 24.99, "status": "Shipped"},
            {"id": "19283", "customer_id": "5190753", "product": "Wireless Mouse", "quantity": 1, "price": 34.99, "status": "Processing"},
            {"id": "74651", "customer_id": "6824095", "product": "Gaming Keyboard", "quantity": 1, "price": 89.99, "status": "Delivered"},
            {"id": "30298", "customer_id": "7135680", "product": "Portable Charger", "quantity": 2, "price": 29.99, "status": "Shipped"},
            {"id": "47652", "customer_id": "8259147", "product": "Smartwatch", "quantity": 1, "price": 199.99, "status": "Processing"},
            {"id": "61984", "customer_id": "9603481", "product": "Noise-Cancelling Headphones", "quantity": 1, "price": 149.99, "status": "Shipped"},
            {"id": "58243", "customer_id": "1057426", "product": "Wireless Earbuds", "quantity": 2, "price": 99.99, "status": "Delivered"},
            {"id": "90357", "customer_id": "1213210", "product": "Smartphone Case", "quantity": 1, "price": 19.99, "status": "Shipped"},
            {"id": "28164", "customer_id": "2837622", "product": "Wireless Headphones", "quantity": 2, "price": 79.99, "status": "Processing"}
        ]

    def get_user(self, key, value):
        if key in {"email", "phone", "username"}:
            for customer in self.customers:
                if customer[key] == value:
                    return customer
            return f"Couldn't find a user with {key} of {value}"
        else:
            raise ValueError(f"Invalid key: {key}")

        return None

    def get_order_by_id(self, order_id):
        for order in self.orders:
            if order["id"] == order_id:
                return order
        return None

    def get_customer_orders(self, user_id):
        return [order for order in self.orders if order["customer_id"] == user_id]

    def cancel_order(self, order_id):
        order = self.get_order_by_id(order_id)
        if order:
            if order["status"] == "Processing":
                order["status"] = "Cancelled"
                return "Cancelled the order"
            else:
                return "Order has already shipped.  Can't cancel it."
        return "Can't find that order!"

db = FakeDatabase()

tools = [
    {
        "name": "get_user",
        "description": "Looks up user details by email, phone, or username.",
        "input_schema": {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "enum": ["email", "phone", "username"],
                    "description": "The attribute to search for a user by (email, phone, or username)."
                },
                "value": {
                    "type": "string",
                    "description": "The value to match for the specified attribute."
                }
            },
            "required": ["key", "value"],
            "returns": "a user object. example: {\"id\": \"1213210\", \"name\": \"John Doe\", \"email\": \"jd@foo.bar\", \"phone\": \"123-456-7890\", \"username\": \"johndoe\"}"
        }
    },
    {
        "name": "get_order_by_id",
        "description": "Retrieves the details of a specific order based on the order ID. Returns the order ID, product name, quantity, price, and order status.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The unique identifier for the order."
                }
            },
            "required": ["order_id"]
        }
    },
    {
        "name": "get_customer_orders",
        "description": "Retrieves the list of orders belonging to a user based on a user's id.",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "The \"id\" of the user"
                }
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "cancel_order",
        "description": "Cancels an order based on a provided order_id.  Only orders that are 'processing' can be cancelled",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The order_id pertaining to a particular order"
                }
            },
            "required": ["order_id"]
        }
    }
]

def process_tool_call(tool_name, tool_input):
    if tool_name == "get_user":
        return db.get_user(tool_input["key"], tool_input["value"])
    elif tool_name == "get_order_by_id":
        return db.get_order_by_id(tool_input["order_id"])
    elif tool_name == "get_customer_orders":
        return {"orders": db.get_customer_orders(tool_input["user_id"])}
    elif tool_name == "cancel_order":
        return db.cancel_order(tool_input["order_id"])


# local_model = "llama3:latest"
# local_model = "llama3:8b-instruct-fp16"
local_model = "llama3:70b"
# local_model = "llama3:70b-instruct-q8_0"
# local_model = "phi3:14b-medium-4k-instruct-f16"
# local_model = "codegemma:7b-code-fp16"
# local_model = "gemma2:27b-instruct-fp16"
# local_model = "qwen2:latest"
# local_model = "qwen2:72b-instruct-q8_0"
# local_model = "mistral:7b-instruct-v0.3-fp16"
# local_model = "adrienbrault/nous-hermes2theta-llama3-8b:f16"
# local_model = "aya:35b-23-f16"
# local_model = "mgmacleod/functionary-small:v2.2-q4_0"

llm = thinker.Ollama(model=local_model,
                     chat=True)

print(color.GRAY_MEDIUM + f"{llm}" + color.END)

# llm = thinker.Claude(model="claude-3-haiku-20240307")

# messages = [{"role": "user", "content": "Can you look up my orders? My email is john@gmail.com"}]

def simple_chat():

    pre_prompt = """
    You are a customer support chat bot for an online retailer called TechNova.
    You can look up customer information, orders, and cancel orders.
    Users can be looked up by: email, phone or username
    Orders can be looked up by order id or user id
    """

    ask_user = True
    messages = [{"role": "system", "content": pre_prompt}]

    while True:

        #If the last message is from the assistant, get another input from the user
        if ask_user:
            user_message = input("\nUser: ")
            messages.append({"role": "user", "content": user_message})
            ask_user = False

        # ser = thinker.serialize_messages(messages)

        say("chat log", f"> {messages}", color.GRAY_DIUM, color.GRAY_ME)

        # ask llm what it thinks
        response = llm.think(messages,
                             temperature=0.2,
                             tools=tools,
                             max_tokens=4096)

        say("chat log", f"< {response}", color.GRAY_DIUM, color.GRAY_ME)

        # if Claude stops because it wants to use a tool:
        if response.stop_reason == "tool_use":

            # find the ToolUseThought in the response content
            tool_use = next((thought for thought in response.content if isinstance(thought, ToolUseThought)), None)

            if tool_use:
                tool_name = tool_use.name
                tool_input = tool_use.input
            else:
                print("no ToolUseThought found in the response.")

            print(f"calling a \"{tool_name}\" tool with: \"{tool_input}\"")

            # Actually run the underlying tool functionality on our db
            tool_result = process_tool_call(tool_name, tool_input)

            say("chat log", f"tool result: {tool_result}", color.GRAY_DIUM, color.GREEN)

            messages.append({"role": "user", "content": f"use this intel: {json.dumps(tool_result)}. if this information is enough to answer just return it without calling tools."})
            ask_user = False

        else:
            # find the TextThought in the response content
            thought = next((thought for thought in response.content if isinstance(thought, TextThought)), None)
            if thought.text is not None:
                messages.append({"role": "assistant", "content": thought.text})

            # If Claude does NOT want to use a tool, just print out the text reponse
            print("\nTechNova Support: " + f"{thought.text}" )
            ask_user = True

simple_chat()
