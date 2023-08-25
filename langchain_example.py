#! env python

import json
import logging
import os
import subprocess
import sys
from typing import Any

from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.chains import ConversationalRetrievalChain, RetrievalQA
from langchain.chat_models import ChatOpenAI
from langchain.document_loaders import DirectoryLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.indexes import VectorstoreIndexCreator
from langchain.indexes.vectorstore import VectorStoreIndexWrapper
from langchain.llms import OpenAI
from langchain.schema import AgentAction, LLMResult
from langchain.vectorstores import Chroma

logger = logging.getLogger(__name__)

# Enable to save to disk & reuse the model (for repeated runs on the same data)
PERSIST = False  # True  # False
STREAMING = False  # True
DEBUG = False
MODEL = "gpt-4"  # "gpt-3.5-turbo",


class StreamTokenMetaData(StreamingStdOutCallbackHandler):
    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """Run on new LLM token. Only available when streaming is enabled."""
        sys.stdout.write(f" {kwargs=}")
        sys.stdout.flush()


def get_local_credentials():
    keypath = subprocess.check_output(
        ".llm_venv/bin/llm keys path".split(), text=True
    ).strip()
    if DEBUG:
        print(keypath)
    with open(keypath) as f:
        return json.load(f)["openai"]


def loop(k=3):
    os.environ["OPENAI_API_KEY"] = os.environ.get(
        "OPENAI_API_KEY", get_local_credentials()
    )

    query = None
    if len(sys.argv) > 1:
        query = sys.argv[1]

    # loader = TextLoader("data/data.txt")
    loader = DirectoryLoader("data/", recursive=True, show_progress=True, glob="*.txt")

    if PERSIST:
        if os.path.exists("persist"):
            print("Reusing index...\n")

            vectorstore = Chroma(
                persist_directory="persist", embedding_function=OpenAIEmbeddings()
            )
        else:
            print("Creating index...\n")

            new_index = VectorstoreIndexCreator().from_loaders([loader])
            new_index.vectorstore.persist("persist")
            vectorstore = new_index.vectorstore

        index = VectorStoreIndexWrapper(vectorstore=vectorstore)

    else:
        index = VectorstoreIndexCreator().from_loaders([loader])

    chain = ConversationalRetrievalChain.from_llm(
        llm=ChatOpenAI(
            model=MODEL,
            streaming=STREAMING,
            callbacks=[
                StreamingStdOutCallbackHandler(),
                # StreamTokenMetaData(),
            ],
            temperature=0.0,
        ),
        retriever=index.vectorstore.as_retriever(
            search_kwargs={"k": k, "return_source_documents": True}
        ),
    )
    # chain.retriever.return_source_documents = True

    chat_history = []  # the simplest memory possible
    while True:
        if not query:
            query = input("\nPrompt (q to quit): ")
        if query in ["quit", "q", "exit"]:
            sys.exit()

        # debugging the retrieval
        if PERSIST:
            # for the persisted chromadb
            found_docs = vectorstore.max_marginal_relevance_search(
                query, k=k, fetch_k=20
            )
        else:
            # breakpoint()
            found_docs = chain.retriever._get_relevant_documents(
                query, run_manager=chain.callback_manager
            )

        if DEBUG:
            for i, doc in enumerate(found_docs):
                print(f"DEBUG: {i + 1}.", doc.page_content, "\n", file=sys.stderr)

        result = chain(
            {
                "system": f"Moderators are speakers."
                f"  Talks, presentations and sessions are the same thing."
                " Remember to answer the question. DO NOT ask questions.",
                "question": f"  {query}",
                "chat_history": chat_history,
            }
        )
        if not STREAMING:
            print(result["answer"])

        chat_history.append((query, result["answer"]))
        query = None


if __name__ == "__main__":
    LOGLEVEL = os.environ.get("LOGLEVEL", "WARNING").upper()
    logging.basicConfig(level=LOGLEVEL)
    loop(k=10)
