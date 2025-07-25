#!/usr/bin/env python3

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    print("Please set OPENAI_API_KEY in your .env file")
    exit(1)

chat_model = ChatOpenAI()
models = chat_model.root_client.models.list()

for model in sorted(models.data, key=lambda x: x.id):
    print(model.id)