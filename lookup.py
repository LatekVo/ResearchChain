from colorama import Fore
from colorama import Style

from langchain_community.llms.ollama import Ollama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.document_loaders import WebBaseLoader

from os.path import exists

import tiktoken

# todo: replace with puppeteer, this one gets blocked occasionally
from googlesearch import search


def purify_name(name):
    return '_'.join('_'.join(name.split(':')).split('-'))


model_name = "zephyr:7b-beta-q5_K_M"  # "llama2-uncensored:7b"
model_safe_name = purify_name(model_name)
token_limit = 4096  # depending on VRAM, try 2048, 3072 or 4096. 2048 works great on 4GB VRAM
llm = Ollama(model=model_name)

embedding_model_name = "nomic-embed-text"
embedding_model_safe_name = purify_name(embedding_model_name)
embeddings = OllamaEmbeddings(model=model_name)

encoder = tiktoken.get_encoding("cl100k_base")
output_parser = StrOutputParser()

if not exists('store/' + embedding_model_safe_name + '.faiss'):
    tmp_db = FAISS.from_texts(['You are a large language model, intended for research purposes.'], embeddings)
    tmp_db.save_local(folder_path='store', index_name=embedding_model_safe_name)

db = FAISS.load_local(folder_path='store', embeddings=embeddings, index_name=embedding_model_safe_name)


def _extract_from_quote(text: str):
    if '"' in text:
        return text.split('"')[1]
    else:
        return text


def _rag_chain_function(prompt_text: str):
    return prompt_text


def _web_query_google_lookup(prompt_text: str, search_type: Literal['info', 'wiki', 'news', 'docs'] = 'news'):
    # defaults - for info
    extra_params = None
    tbs = 0
    pre_prompt = None

    if search_type == 'wiki':
        pre_prompt = 'wikipedia'
    elif search_type == 'news':
        extra_params = {
            'tbm': 'nws',  # news only
        }
        tbs = 'qdr:m'  # last month only
    elif search_type == 'docs':
        pre_prompt = 'documentation '

    prompt_text = f"{pre_prompt}{_extract_from_quote(prompt_text)}"

    print(f"{Fore.CYAN}{Style.BRIGHT}Searching for:{Style.RESET_ALL}", f"{pre_prompt}{prompt_text}")

    url_list = list(
        search(
            query=f"{pre_prompt}{prompt_text}",
            stop=5, lang='en', safe='off', tbs=tbs, extra_params=extra_params))

    print(f"{Fore.CYAN}Web search completed.{Fore.RESET}")

    # download and embed all of the documents
    for url in url_list:
        documents = WebBaseLoader(url).load_and_split(RecursiveCharacterTextSplitter())
        db.add_documents(documents, embeddings=embeddings)
    db.save_local(folder_path='store', index_name=embedding_model_safe_name)

    print(f"{Fore.CYAN}Document vectorization completed.{Fore.RESET}")

    # return the document with the highest prompt similarity score (for now only browsing the first search result)
    embedding_vector = embeddings.embed_query(prompt_text)
    docs_and_scores = db.similarity_search_by_vector(embedding_vector)

    print(f"{Fore.CYAN}Database search completed.{Fore.RESET}")

    context_text = ""
    token_count = 0
    document_index = 0
    while token_count < token_limit:
        token_count += len(encoder.encode(docs_and_scores[document_index].page_content))
        context_text += docs_and_scores[document_index].page_content
        document_index += 1
        if document_index >= len(docs_and_scores):
            return context_text

    # returning top 3 best results
    return context_text


def _web_chain_function(prompt_dict: dict):
    # TODO: news searches should strictly search for news fresher than 1 month / 1 week
    # TODO: news crawling should be done through only sites like medium, which are much more dense than google
    # TODO: create a different function + prompt for documentation / facts searching, and make this one news focused
    web_interpret_prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are a search results interpreter. Your job is to write an article based on the provided context."
         "Your job is to convert all the search results you were given into a long, comprehensive and clean output."
         "Use provided search results data to answer the user request to the best of your ability."),
        ("user", "Search results data: "
                 "```"
                 "{search_data}"
                 "```"
                 "User request: \"Write an article on: {user_request}\"")
    ])

    def get_user_prompt(_: dict):
        return prompt_dict['input']

    # NOTE: a detour has been performed here, more details:
    #       web_chain_function will soon become just a tool playing a part of a larger mechanism.
    #       prompt creation will be taken over by prompt sentiment extractor which will extract all researchable
    #       queries from the user prompt, and start separate chains performing those steps in parallel
    #       until a satisfactory response is created.

    chain = (
        {
            "search_data": RunnableLambda(get_user_prompt) | RunnableLambda(_web_query_google_lookup),
            "user_request": RunnableLambda(get_user_prompt)  # this has to be a RunnableLambda, it cannot be a string
        } |
        web_interpret_prompt |
        llm |
        output_parser
    )

    return chain.invoke(prompt_dict)


rag_lookup = RunnableLambda(_rag_chain_function)
web_lookup = RunnableLambda(_web_chain_function)


def _lookup_determining_proxy(prompt_input: str):
    web_chain = web_lookup
    if 'google' in prompt_input.lower():
        web_chain.invoke({'input': prompt_input})
    return prompt_input


lookup_parser = RunnableLambda(_lookup_determining_proxy)
