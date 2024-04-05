from typing import List

import requests.exceptions
import tiktoken
from googlesearch import search
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores.faiss import FAISS
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from colorama import Fore, Style
from core.tools.model_loader import load_model
from core.models.configurations import use_configuration
from core.tools.utils import purify_name
from core.tools.dbops import get_db_by_name
from core.classes.query import WebQuery
from core.tools.utils import is_text_junk, remove, timeout_function

encoder = tiktoken.get_encoding("cl100k_base")
output_parser = StrOutputParser()

llm, embeddings = load_model()
llm_config, embed_config = use_configuration()
embedding_model_safe_name = purify_name(embed_config.model_name)


def docs_to_context(docs_and_scores: List[Document], token_limit: int) -> str:
    context_text = ""
    token_count = 0
    document_index = 0
    while token_count < token_limit:
        token_count += len(encoder.encode(docs_and_scores[document_index].page_content))
        context_text += docs_and_scores[document_index].page_content
        document_index += 1
        if document_index >= len(docs_and_scores):
            break

    print(f"{Fore.CYAN}Used {document_index + 1} snippets with a total of {token_count} tokens as context.{Fore.RESET}")
    print(f"{Fore.CYAN}Context itself: {Fore.RESET}", context_text)
    return context_text


def rag_query_lookup(prompt_text: str) -> str:
    pass


def populate_db_with_google_search(database: FAISS, query: WebQuery):
    print(f"{Fore.CYAN}{Style.BRIGHT}Searching for:{Style.RESET_ALL}", query.web_query)

    url_list = search(
        query=query.web_query,
        stop= embed_config.article_limit,
        lang='en',
        safe='off',
        tbs=query.web_tbs,
        extra_params=query.web_extra_params)

    print(f"{Fore.CYAN}Web search completed.{Fore.RESET}")

    for url in url_list:
        url_handle = WebBaseLoader(url)

        # try downloading web content
        try:
            # fixme: certain sites load forever, soft-locking this loop (prompt example: car)
            document = url_handle.load()
        except requests.exceptions.ConnectionError:
            continue

        if document is None:
            continue

        text_splitter = RecursiveCharacterTextSplitter(
            separators=embed_config.buffer_stops,
            chunk_size=query.db_chunk_size,
            chunk_overlap=embed_config.chunk_overlap,
            keep_separator=False,
            strip_whitespace=True)

        chunks = text_splitter.split_documents(document)

        for chunk in chunks:
            if is_text_junk(chunk.page_content):
                chunks.remove(chunk)
                continue

            chunk.page_content = remove(chunk.page_content, ['\n', '`'])
            chunk.page_content = (query.db_embedding_prefix +
                                  chunk.page_content +
                                  query.db_embedding_postfix)

        if len(chunks) != 0:
            database.add_documents(documents=chunks, embeddings=embeddings)

    db_name = embedding_model_safe_name + query.db_save_file_extension
    database.save_local(folder_path='store/vector', index_name=db_name)

    print(f"{Fore.CYAN}Document vectorization completed.{Fore.RESET}")


def web_query_google_lookup(query: WebQuery, token_limit: int = embed_config.model_token_limit):
    db_name = embedding_model_safe_name + query.db_save_file_extension
    db = get_db_by_name(db_name, embeddings)

    populate_db_with_google_search(db, query)

    # return the document with the highest prompt similarity score (for now only browsing the first search result)
    embedding_vector = embeddings.embed_query(query.db_embed_query)
    docs_and_scores = db.similarity_search_by_vector(embedding_vector, k=round(token_limit / 64))

    print(f"{Fore.CYAN}Database search completed.{Fore.RESET}")

    return docs_to_context(docs_and_scores, llm_config.model_token_limit)
