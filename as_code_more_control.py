#! env python
import asyncio
import json
import os
import subprocess
import sys

import openai
from langchain.chains import ConversationalRetrievalChain, RetrievalQA
from langchain.chat_models import ChatOpenAI
from langchain.document_loaders import DirectoryLoader, TextLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.indexes import VectorstoreIndexCreator
from langchain.indexes.vectorstore import VectorStoreIndexWrapper
from langchain.llms import OpenAI
from langchain.vectorstores import Chroma


def get_local_credentials():
    keypath = subprocess.check_output(
        ".venv/bin/llm keys path".split(), text=True
    ).strip()
    print(keypath)
    with open(keypath) as f:
        return json.load(f)["openai"]


async def loop(k=3):
    os.environ["OPENAI_API_KEY"] = os.environ.get(
        "OPENAI_API_KEY", get_local_credentials()
    )

    # Enable to save to disk & reuse the model (for repeated queries on the same data)
    # PERSIST = True
    PERSIST = False

    query = None
    if len(sys.argv) > 1:
        query = sys.argv[1]

    # loader = TextLoader("data/data.txt") # Use this line if you only need data.txt
    loader = DirectoryLoader("data/", recursive=True, show_progress=True, glob="*.txt")

    if PERSIST and os.path.exists("persist"):
        print("Reusing index...\n")

        vectorstore = Chroma(
            persist_directory="persist", embedding_function=OpenAIEmbeddings()
        )
        index = VectorStoreIndexWrapper(vectorstore=vectorstore).from_loaders([loader])
    else:
        index = VectorstoreIndexCreator().from_loaders([loader])

    chain = ConversationalRetrievalChain.from_llm(
        llm=ChatOpenAI(model="gpt-3.5-turbo"),
        retriever=index.vectorstore.as_retriever(
            search_kwargs={"k": k, "return_source_documents": True}
        ),
    )
    # chain.retriever.return_source_documents = True

    chat_history = []  # the simplest memory possible
    while True:
        if not query:
            query = input("Prompt: ")
        if query in ["quit", "q", "exit"]:
            sys.exit()

        # debugging the retrieval
        if PERSIST:
            # for the persisted chromadb
            found_docs = await vectorstore.amax_marginal_relevance_search(
                query, k=k, fetch_k=10
            )
        else:
            # breakpoint()
            found_docs = chain.retriever._get_relevant_documents(
                query, run_manager=chain.callback_manager
            )

        for i, doc in enumerate(found_docs):
            print(f"DEBUG: {i + 1}.", doc.page_content, "\n")

        result = chain({"question": query, "chat_history": chat_history})
        print(result["answer"])

        chat_history.append((query, result["answer"]))
        query = None


import logging
import os

if __name__ == "__main__":
    LOGLEVEL = os.environ.get("LOGLEVEL", "WARNING").upper()
    logging.basicConfig(level=LOGLEVEL)
    asyncio.run(loop(k=10))
