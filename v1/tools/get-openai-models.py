#!/usr/bin/env python3

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    print("Please set OPENAI_API_KEY in your .env file")
    exit(1)

# Local static pricing data (USD per 1K tokens)
# prices as of Aug 8, 2025 from https://platform.openai.com/docs/pricing?latest-pricing=standard
#
model_prices = {
    "gpt-5":                        {"input": 1.25,  "output": 10.00},
    "gpt-5-mini":                   {"input": 0.25,  "output": 2.00},
    "gpt-5-nano":                   {"input": 0.05,  "output": 0.40},
    "gpt-5-chat-latest":           {"input": 1.25,  "output": 10.00},
    "gpt-4.1":                      {"input": 2.00,  "output": 8.00},
    "gpt-4.1-mini":                 {"input": 0.40,  "output": 1.60},
    "gpt-4.1-nano":                 {"input": 0.10,  "output": 0.40},
    "gpt-4o":                       {"input": 2.50,  "output": 10.00},
    "gpt-4o-2024-05-13":            {"input": 5.00,  "output": 15.00},
    "gpt-4o-realtime-preview":     {"input": 5.00,  "output": 20.00},
    "gpt-4o-mini":                 {"input": 0.15,  "output": 0.60},
    "gpt-4o-mini-realtime-preview":{"input": 0.60,  "output": 2.40},
    "o1":                           {"input": 15.00, "output": 60.00},
    "o3":                           {"input": 2.00,  "output": 8.00},
    "o3-deep-research":            {"input": 10.00, "output": 40.00},
    "o4-mini":                     {"input": 1.10,  "output": 4.40},
    "o4-mini-deep-research":       {"input": 2.00,  "output": 8.00},
    "o3-mini":                     {"input": 1.10,  "output": 4.40},
    "o1-mini":                     {"input": 1.10,  "output": 4.40},
    "codex-mini-latest":           {"input": 1.50,  "output": 6.00},
}

# Models allowed to be used with completions endpoint (manual mapping)
completion_compatible_ids = {
    "davinci-002", "gpt-3.5-turbo", "gpt-3.5-turbo-0125", "gpt-3.5-turbo-1106",
    "gpt-3.5-turbo-16k", "gpt-3.5-turbo-instruct", "gpt-3.5-turbo-instruct-0914",
    "gpt-4", "gpt-4-0125-preview", "gpt-4-0613", "gpt-4-1106-preview",
    "gpt-4-turbo", "gpt-4-turbo-2024-04-09", "gpt-4-turbo-preview"
}

# Initialize OpenAI client via LangChain
chat_model = ChatOpenAI()
models = chat_model.root_client.models.list()

# Filter models
filtered_models = [
    m for m in models.data
    if m.id.startswith("gpt-") or m.id in completion_compatible_ids
]

# Build table
rows = []
for model in sorted(filtered_models, key=lambda x: x.id):
    model_id = model.id
    pricing = model_prices.get(model_id)
    if pricing:
        total_cost = pricing["input"] + pricing["output"]
        rows.append((model_id, f"${total_cost:.4f}"))
    else:
        rows.append((model_id, "n/a"))

# Print markdown-style table
print(f"| {'model_name':<40} | {'total_cost_in1000_out_1000':<28} |")
print(f"|{'-'*42}|{'-'*30}|")
for model_id, cost in rows:
    print(f"| {model_id:<40} | {cost:<28} |")