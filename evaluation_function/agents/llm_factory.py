import os
import getpass

from langchain_openai import AzureChatOpenAI
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.llms import Ollama
from langchain_community.embeddings import OllamaEmbeddings
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings

class AzureLLMs:
    def __init__(self):
        self._azure_llm = AzureChatOpenAI(
                        openai_api_version=os.environ["AZURE_OPENAI_API_VERSION"],
                        azure_deployment=os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"],
                        temperature=0,
                        max_tokens=None,
                    )
        self._azure_embedding = AzureOpenAIEmbeddings(azure_deployment=os.environ['AZURE_OPENAI_EMBEDDING_1536_DEPLOYMENT'], 
                                        openai_api_version=os.environ["AZURE_OPENAI_API_VERSION"],
                                        model=os.environ["AZURE_OPENAI_EMBEDDING_1536_MODEL"])

    def get_llm(self):    
        return self._azure_llm

    def get_embedding(self):
        return self._azure_embedding

class OllamaLLMs:
    def __init__(self):
        self._ollama_llm = Ollama(
            model=os.environ['OLLAMA_MODEL'], # Any of the available models listed in the API docs
            base_url=os.environ['OLLAMA_BASE_URL'],
            headers={
                'X-API-Key': os.environ['OLLAMA_API_KEY'],
            },
        )

        self._ollama_embedding = OllamaEmbeddings(
            model='nomic-embed-text:137m-v1.5-fp16',
            base_url=os.environ['OLLAMA_BASE_URL'],
            headers={
                'X-API-Key': os.environ['OLLAMA_API_KEY'],
            },
            show_progress=True
        )

    def get_llm(self):
        return self._ollama_llm

    def get_embedding(self):
        return self._ollama_embedding
    
class OpenAILLMs:
    def __init__(self):
        if "OPENAI_API_KEY" not in os.environ:
            os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter your OpenAI API key: ")

        self._openai_llm = ChatOpenAI(
            model=os.environ['OPENAI_MODEL'],
            temperature=0,
            api_key=os.environ["OPENAI_API_KEY"],
        )

        self._openai_embedding = OpenAIEmbeddings(
            model='text-embedding-ada-002',
            api_key=os.environ['OPENAI_API_KEY'],
        )
    
    def get_llm(self):
        return self._openai_llm
    
    def get_embedding(self):
        return self._openai_embedding