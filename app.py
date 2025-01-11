import re
from flask import Flask, render_template, request
from search import Search
import asyncio

from llama_index.core import Settings
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama


ollama_embedding = OllamaEmbedding("llama3")
Settings.embed_model = ollama_embedding
local_llm = Ollama(model="llama3")

app = Flask(__name__)
es = Search()


def extract_filters(query):
    filters = []

    filter_regex = r'category:([^\s]+)\s*'
    m = re.search(filter_regex, query)
    if m:
        filters.append({
            'term': {
                'category.keyword': {
                    'value': m.group(1)
                }
            }
        })
        query = re.sub(filter_regex, '', query).strip()

    return {'filter': filters}, query


@app.get('/')
def index():
    return render_template('index.html')


@app.post('/')
def handle_search():
    query = request.form.get('query', '')
    print(f"Query: {query}")

    filters, parsed_query = extract_filters(query)
    embeddings = es.get_embedding(parsed_query)

    print(f"Filters: {filters}")
    print(f"Parsed query: {parsed_query}")

    from_ = request.form.get('from_', type=int, default=0)

    results = es.search(
        knn={
            'field': 'embedding',
            'query_vector': embeddings,
            'k': 10,
            'num_candidates': 50,
            **filters,
        },
        # rank={
        #    'rrf': {}
        # },
        size=5,
        from_=from_
    )

    print(f"Results: {results['hits']['hits']}")

    return render_template('index.html', results=results['hits']['hits'],
                           query=query, from_=from_,
                           total=results['hits']['total']['value'], aggs={})


@app.post('/llm')
def handle_llm_search():
    query = request.form.get('query', '')
    print(f"Query: {query}")

    llm_result = es.search_llm(query)
    print(f"Result from LLM: {llm_result}")

    return render_template('index.html', results=[llm_result],
                           query=query, from_=1,
                           total=1, aggs={})


@app.get('/document/<id>')
def get_document(id):
    document = es.retrieve_document(id)
    paragraphs = document['_source']['message'].split('\n')
    return render_template('document.html', title="Document", paragraphs=paragraphs)
