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
from prompt_toolkit import PromptSession
from prompt_toolkit import prompt as input
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.bindings.vi import load_vi_bindings


#

logger = logging.getLogger(__name__)

# Enable to save to disk & reuse the model (for repeated runs on the same data)
PERSIST = True  # False
STREAMING = True
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
            print("Loading index...\n")

            persistent_vectorstore = Chroma(
                persist_directory="persist", embedding_function=OpenAIEmbeddings()
            )
            index = VectorStoreIndexWrapper(vectorstore=persistent_vectorstore)

        else:
            print("Creating index...\n")
            vsic = VectorstoreIndexCreator(
                vectorstore_cls=Chroma,
                vectorstore_kwargs={
                    # "persist": True,
                    "persist_directory": "persist",
                    # "embedding_function": OpenAIEmbeddings(),
                },
            )
            index = vsic.from_loaders([loader])

    else:
        print("creating in-memory index...\n")
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

    chat_history = []  # the simplest memory possible
    prompt_session = PromptSession(
        enable_history_search=True,
    )

    conference_completer = WordCompleter(
        [
            "Rally Innovation",
            "conference",
            "talk",
            "presentation",
            "session",
            "moderator",
            "speaker",
        ]
    )
    vim_bindings = load_vi_bindings()

    while True:
        if not query:
            query = prompt_session.prompt(
                [
                    ("class:prompt", "\n\nPrompt (q to quit): "),
                ],
                style=Style.from_dict(
                    {
                        "prompt": "#00ff66",
                    }
                ),
                completer=conference_completer,
                complete_while_typing=False,
                key_bindings=vim_bindings,
            )

        if query in [":q", "quit", "q", "exit"]:
            sys.exit()

        # debugging the retrieval
        if PERSIST:
            # for the persisted chromadb
            found_docs = index.vectorstore.max_marginal_relevance_search(
                query, k=k, fetch_k=20
            )
        else:
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
