import os
from dotenv import load_dotenv
from elasticsearch import Elasticsearch, AsyncElasticsearch
from sentence_transformers import SentenceTransformer

# llama
from llama_index.vector_stores.elasticsearch import ElasticsearchStore
from llama_index.core import VectorStoreIndex, QueryBundle, Settings
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama

load_dotenv()

ES_USERNAME = os.environ['ES_USERNAME']
ES_PASSWORD = os.environ['ES_PASSWORD']
INDEX_NAME_KNN = os.environ['INDEX_NAME_KNN']
INDEX_NAME_LLAMA = os.environ['INDEX_NAME_LLAMA']


class Search:
    def __init__(self):
        self.es = Elasticsearch(hosts='http://localhost:9200', basic_auth=(ES_USERNAME, ES_PASSWORD))
        client_info = self.es.info()
        print('Connected to Elasticsearch!')
        print(client_info.body)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def get_embedding(self, text):
        return self.model.encode(text)

    def insert_document(self, document):
        return self.es.index(index=INDEX_NAME, document={
            **document,
            'embedding': self.get_embedding(document['summary']),
        })

    def insert_documents(self, documents):
        operations = []
        for document in documents:
            operations.append({'index': {'_index': 'tickers-embeddings'}})
            operations.append({
                **document,
                'embedding': self.get_embedding(document['summary']),
            })
        return self.es.bulk(operations=operations)

    def retrieve_document(self, id):
        return self.es.get(index=INDEX_NAME, id=id)

    def search(self, **query_args):
        return self.es.search(index=INDEX_NAME_KNN, **query_args)

    def search_llm(self, query):
        Settings.embed_model = OllamaEmbedding(model_name="llama3")
        local_llm = Ollama(model="llama3")

        async_es_client = AsyncElasticsearch(hosts='http://localhost:9200', basic_auth=(ES_USERNAME, ES_PASSWORD))
        es_vector_store = ElasticsearchStore(
            index_name=INDEX_NAME_LLAMA,
            vector_field='embedding',
            text_field='message',
            es_client=async_es_client
        )

        index = VectorStoreIndex.from_vector_store(es_vector_store)

        query_engine = index.as_query_engine(local_llm, similarity_top_k=10)
        embeddings = Settings.embed_model.get_query_embedding(query=query)
        print(f"embeddings size: {len(embeddings)}")
        bundle = QueryBundle(query_str=query, embedding=embeddings)
        response = query_engine.query(bundle)

        print(f"response: {response}")
        return response
