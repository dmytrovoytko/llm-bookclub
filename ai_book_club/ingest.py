import os
from glob import glob
import pandas as pd
from dotenv import load_dotenv

try:
    from sentence_transformers import SentenceTransformer
    from elasticsearch import Elasticsearch
except:
    pass

import minsearch


load_dotenv()

DEBUG = True # False

USE_ELASTIC = os.getenv("USE_ELASTIC")
ELASTIC_URL = os.getenv("ELASTIC_URL")
ELASTIC_URL_LOCAL = os.getenv("ELASTIC_URL_LOCAL")
# TODO test other model?
INDEX_MODEL_NAME = os.getenv("INDEX_MODEL_NAME", "multi-qa-MiniLM-L6-cos-v1")
INDEX_NAME = os.getenv("INDEX_NAME", "book-reviews")
DATA_PATH = os.getenv("DATA_PATH", "data")
# TODO url?
BASE_URL = "https://github.com/dmytrovoytko/llm-bookclub/blob/main"

def fetch_documents(data_path=DATA_PATH):
    print("Fetching documents...")
    # # TODO index other dataset files from repo
    # docs_url = relative_url # f"{BASE_URL}/{relative_url}?raw=1"
    # # docs_response = requests.get(docs_url)
    # # documents = docs_response.json()
    # df = pd.read_csv(docs_url)
    df = pd.DataFrame()
    data_path = data_path.rstrip('/') # prevent //
    qna_files = sorted(glob(data_path+'/book-reviews-*.csv'))
    for file_name in qna_files:
        df_ = pd.read_csv(file_name) #, index_col=False)
        print(f' adding {file_name}: {df_.shape[0]} record(s)')
        df = pd.concat([df, df_]) #,ignore_index=True)

    documents = df.to_dict(orient="records")
    print(f" Fetched {len(documents)} document(s)")
    return documents

## MINSEARCH

def load_index(data_path=DATA_PATH):
    documents = fetch_documents(data_path)

    index = minsearch.Index(
        text_fields=[
            "author",
            "title",
            "text",
            "category",
        ],
        keyword_fields=["id"],
    )

    index.fit(documents)
    return index

## ELASTIC SEARCH

def setup_elasticsearch():
    try:
        print(f"Setting up Elasticsearch ({ELASTIC_URL})...")
        es_client = Elasticsearch(ELASTIC_URL)
    except:
        print(f"Setting up Elasticsearch ({ELASTIC_URL_LOCAL})...")
        es_client = Elasticsearch(ELASTIC_URL_LOCAL)
    print(" Connected to Elasticsearch:", es_client.info())

    # NB !!! Avoid using the term query for text fields !!!
    index_settings = {
        "settings": {"number_of_shards": 1, "number_of_replicas": 0},
        "mappings": {
            "properties": {
                "author": {"type": "text"},
                "title": {"type": "text"},
                "text": {"type": "text"},
                "category": {"type": "keyword"},
                "id": {"type": "keyword"},
                "title_text_vector": {
                    "type": "dense_vector",
                    "dims": 384,
                    "index": True,
                    "similarity": "cosine",
                },
            }
        },
    }

    try:
        es_client.indices.delete(index=INDEX_NAME, ignore_unavailable=True)
    except Exception as e:
        print('!! es_client.indices.delete:', e)
    es_client.indices.create(index=INDEX_NAME, body=index_settings)
    print(f"Elasticsearch index '{INDEX_NAME}' created")
    return es_client


def load_model():
    print(f"Loading model: {INDEX_MODEL_NAME}")
    return SentenceTransformer(INDEX_MODEL_NAME)


def index_documents(es_client, documents, model):
    print("Indexing documents...")
    for doc in documents:
        author = doc["author"]
        title = doc["title"]
        text = doc["text"]
        try:
            doc["title_text_vector"] = model.encode(author + " " + title + " " + text).tolist() 
            es_client.index(index=INDEX_NAME, document=doc)
        except:
            print('!!! Failed to index:', author + " " + title + " " + text)

    print(f" Indexed {len(documents)} documents")


def init_elasticsearch():
    # you may consider to comment <start>
    # if you just want to init the db or didn't want to re-index
    print("ElasticSearch: starting the indexing process...")

    documents = fetch_documents()
    model = load_model()
    es_client = setup_elasticsearch()
    index_documents(es_client, documents, model)
    # you may consider to comment <end>

    # print("Initializing database...")
    # init_db()

    print(" Indexing process completed successfully!")
    return es_client

SEARCH_RESULTS_NUM = 3 # 5

# TODO from app_rag import elastic_search_text ? & knn
# TODO fine tune weights
def elastic_search_text(query, category, index_name=INDEX_NAME):
    """
    NB !!! Avoid using the term query for text fields !!!
    By default, Elasticsearch changes the values of text fields during analysis. For example, the default standard analyzer changes text field values as follows:
        Removes most punctuation
        Divides the remaining content into individual words, called tokens
        Lowercases the tokens
    """
    search_query = {
        "size": SEARCH_RESULTS_NUM,
        "query": {
            "bool": {
                "must": {
                    "multi_match": {
                        "query": query,
                        "fields": ["text^2", "title", "author^2"],
                        "type": "best_fields",
                    }
                },
                "filter": {"term": {"category": category}},
            }
        },
    }

    response = es_client.search(index=index_name, body=search_query)
    return [hit["_source"] for hit in response["hits"]["hits"]]


def elastic_search_knn(field, vector, category, index_name=INDEX_NAME):
    # NB !!! Avoid using the term query for text fields !!!
    knn = {
        "field": field,
        "query_vector": vector,
        "k": SEARCH_RESULTS_NUM,
        "num_candidates": 10000,
        "filter": {"term": {"category": category}},
    }

    search_query = {
        "knn": knn,
        "_source": ["author", "title", "text", "category", "id"],
    }

    response = es_client.search(index=index_name, body=search_query)

    return [hit["_source"] for hit in response["hits"]["hits"]]


if __name__ == "__main__":
    if USE_ELASTIC: 
        try:
            es_client = init_elasticsearch()
            if DEBUG:
                # quick test
                category = 'bm' # 'Business & Money'
                query = 'What books were written by Benjamin Hardy?'
                print('\nTest query:', query)
                for search_type in ['Text', 'Vector']: 
                    if search_type == 'Vector':
                        index_model = load_model()
                        vector = index_model.encode(query)
                        search_results = elastic_search_knn('title_text_vector', vector, category)
                    else:
                        search_results = elastic_search_text(query, category)
                    print(search_type, len(search_results), search_results)    
        except Exception as e:
            print("!!! ElasticSearch init error:", e)
    else:
        print("MinSearch: Ingesting data...")
        index = load_index(data_path=DATA_PATH)
        print(f' Indexed {len(index.docs)} document(s)')

        if DEBUG:
            # quick test
            category = 'bm' # 'Business & Money'
            query = 'What books were written by Benjamin Hardy?'
            print('\nTest query:', query)
            search_results = index.search(query, {'category': category}, num_results=3)
            print(len(search_results), search_results)    
