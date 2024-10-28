import os
import time
import json

from openai import OpenAI

from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer


ELASTIC_URL = os.getenv("ELASTIC_URL", "http://elasticsearch:9200")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434/v1/")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-api-key-here")
INDEX_MODEL_NAME = os.getenv("INDEX_MODEL_NAME", "multi-qa-MiniLM-L6-cos-v1")
INDEX_NAME = os.getenv("INDEX_NAME", "book-reviews")
SEARCH_RESULTS_NUM = 7 # 5
CONTEXT_NUM = 3

es_client = Elasticsearch(ELASTIC_URL)
ollama_client = OpenAI(base_url=OLLAMA_URL, api_key="ollama")
openai_client = OpenAI(api_key=OPENAI_API_KEY)
MODEL_NAME = os.getenv("MODEL_NAME") # "ollama/phi3.5" # openai/gpt-4o-mini

categories = {"Business & Money":"bm", "Health, Fitness & Dieting":"hfd", "Science & Math":"sm", "Self-Help":"sh"}

index_model = SentenceTransformer(INDEX_MODEL_NAME)

DEBUG = True

def print_log(message):
    print(message) # let's check without it // , flush=True)

def get_category(category_choice):
    category = categories.get(category_choice, "bm")
    return category

def get_category_name(category_keyword):
    for category in categories:
        if categories[category] == category_keyword:
            return category
    return categories.keys()[0] # as default


def elastic_search_text(query, category, index_name=INDEX_NAME):
    if DEBUG:
        print('elastic_search_text', category)
    search_query = {
        "size": SEARCH_RESULTS_NUM,
        "query": {
            "bool": {
                "must": {
                    "multi_match": {
                        "query": query,
                        "fields": ["text^6", "title^6", "author^4"],
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
    if DEBUG:
        print('elastic_search_knn', category)
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

    es_results = es_client.search(index=index_name, body=search_query)

    return [hit["_source"] for hit in es_results["hits"]["hits"]]

def response_length_prompt(max_length):
    # simplified - without using additional LLM call, as it is slow with Ollama
    if max_length<=200:
        return f"Responses should be brief and concise with minimal narration. One paragraph, no more than three sentences, no more than {max_length} words." 
    elif max_length<=500:
        return f"Responses should be with minimal narration. Two paragraphs, no more than three sentences each, no more than {max_length} words." 
    else: #if max_length<=1000:
        return f"Responses should be thorough and well structured, no more than {max_length} words." 

def build_prompt(query, category_choice, search_results, max_length):
    # limit max_length
    # simplified user query rewriting to manage output length
    # using parameters like max_tokens doesn't work for all Ollama models
    response_limits = response_length_prompt(max_length)
    # TODO refine prompt
    prompt_template = """
You're an experienced book reviewer who is reading all Amazon bestsellers and helping readers to get insights about books in {category_choice} category. Answer the QUESTION based on the CONTEXT from our knowledge database.
Use only the facts from the CONTEXT when answering the QUESTION.
{response_limits}

QUESTION: {question}

CONTEXT: 
{context}
""".strip()

    context = "\n\n".join(
        [
            f"\nbook category: {get_category_name(doc['category'])}\nauthor: {doc['author']}\ntitle: {doc['title']}\nreview: {doc['text']}"
            for doc in search_results
        ]
    )

    prompt = prompt_template.format(question=query, category_choice=category_choice, context=context, response_limits=response_limits).strip()
    if DEBUG:
        print_log(f'Search_results: {len(search_results)}')
        print_log(f'Prompt: {max_length} {prompt}')
        # print_log(f'Context: {context}') # DEEP DEBUG
    return prompt


def llm(prompt, model_choice, max_length=100):
    # TODO max_length in tokens?
    start_time = time.time()
    if model_choice.startswith('ollama/'):
        response = ollama_client.chat.completions.create(
            model=model_choice.split('/')[-1],
            messages=[{"role": "user", "content": prompt}]
        )
        answer = response.choices[0].message.content
        tokens = {
            'prompt_tokens': response.usage.prompt_tokens,
            'completion_tokens': response.usage.completion_tokens,
            'total_tokens': response.usage.total_tokens
        }
    # TODO add microsoft/phi via HF
    elif model_choice.startswith('openai/'):
        response = openai_client.chat.completions.create(
            model=model_choice.split('/')[-1],
            messages=[{"role": "user", "content": prompt}]
        )
        answer = response.choices[0].message.content
        tokens = {
            'prompt_tokens': response.usage.prompt_tokens,
            'completion_tokens': response.usage.completion_tokens,
            'total_tokens': response.usage.total_tokens
        }
    else:
        raise ValueError(f"Unknown model choice: {model_choice}")
    
    response_time = time.time() - start_time
    
    return answer, tokens, response_time


def evaluate_relevance(question, answer):
    evaluation_prompt_template = """
    You are an expert evaluator for a Retrieval-Augmented Generation (RAG) system.
    Your task is to analyze the relevance of the generated answer to the given question.
    Based on the relevance of the generated answer, you will classify it
    as "NON_RELEVANT", "PARTLY_RELEVANT", or "RELEVANT".

    Here is the data for evaluation:

    Question: {question}
    Generated Answer: {answer}

    Please analyze the content and context of the generated answer in relation to the question
    and provide your evaluation in parsable JSON without using code blocks:

    {{
      "Relevance": "NON_RELEVANT" | "PARTLY_RELEVANT" | "RELEVANT",
      "Explanation": "[Provide a brief explanation for your evaluation]"
    }}
    """.strip()

    prompt = evaluation_prompt_template.format(question=question, answer=answer)
    evaluation, tokens, _ = llm(prompt, MODEL_NAME) # 'openai/gpt-4o-mini'

    if DEBUG:
        print_log(f'Evaluation: {evaluation}')
    
    if evaluation.startswith('```json'):
        # remove extra formatting ```json ... ```
        evaluation = evaluation[7:-3].strip()
        # print('evaluate_relevance', evaluation)

    try:
        json_eval = json.loads(evaluation)
        return json_eval['Relevance'], json_eval['Explanation'], tokens
    except:
        print('!! evaluation parsing failed:', evaluation)
        if evaluation.find("RELEVANT")>=0:
            return "RELEVANT", evaluation, tokens
        elif evaluation.find("PARTLY_RELEVANT")>=0:
            return "PARTLY_RELEVANT", evaluation, tokens
        elif evaluation.find("NON_RELEVANT")>=0:
            return "NON_RELEVANT", evaluation, tokens
        else:
            return "UNKNOWN", f"Failed to parse evaluation. {evaluation}", tokens


def calculate_openai_cost(model, tokens):
    openai_cost = 0
    # TODO update costs
    if model == 'openai/gpt-3.5-turbo':
        openai_cost = (tokens['prompt_tokens'] * 0.0015 + tokens['completion_tokens'] * 0.002) / 1000
    elif model in ['openai/gpt-4o', 'openai/gpt-4o-mini']:
        openai_cost = (tokens['prompt_tokens'] * 0.03 + tokens['completion_tokens'] * 0.06) / 1000

    return openai_cost


def get_answer(query, category_choice, author_choice, model_choice, search_type, response_length):
    category = get_category(category_choice)
    if DEBUG:
        print('get_answer category:', category)

    if search_type in ['Vector', 'Hybrid']:
        vector = index_model.encode(query)
        search_results = elastic_search_knn('title_text_vector', vector, category)
        if search_type == "Hybrid":
            # Improve RAG Retrieval - Hybrid search
            # in addition to vector also search text and combine
            tsearch_results = elastic_search_text(query, category)
            if DEBUG:
                print_log(f'Hybrid: v {len(search_results)} + t {len(tsearch_results)}')
                # print(tsearch_results[0])
                # print(search_results[0])
            # add only items not present in the current search results 
            for t in tsearch_results:
                found = False
                for v in search_results:
                    if t['id']==v['id']:
                        found = True
                        break
                if not found:
                    search_results.append(t)
            print_log(f'combined de-duplicated: {len(search_results)}')
            # TODO ?should we also sort them by helpful_vote?

    else: # Text or Hybrid
        search_results = elastic_search_text(query, category)

    # Simplified Reranking 
    # sometimes search ranks reviews for other authors' books higher than chosen one
    # we need to filter out non-relevant reviews 
    # simplified - without using additional LLM call, as it is slow with Ollama
    if author_choice:
        # if author is chosen we can filter out non relevant search results as they mislead LLM
        reranked_results = [doc for doc in search_results if doc['author'] == author_choice]
    else:
        reranked_results = search_results

    # TODO ?Add Fuzzy search option in UI?
    # what should we do if 0 search results for a given query? 
    # stop irrelevant query fast (without calling LLM)?
    #  or add most helpful reviews for the chosen author anyway 
    #       and let LLM figure it out
    # if len(reranked_results)>0 and <CONTEXT_NUM:
    #   add top reviews to have CONTEXT_NUM  

    if DEBUG:
        print_log(f'search_results: {len(search_results)}')
        print_log(f'reranked_results: {len(reranked_results)}')
        print_log([doc['id'] for doc in reranked_results])

    if len(reranked_results)==0:
        return {
            'answer': f'No relevant results found for this query & author ({author_choice})',
            'response_time': 0,
            'relevance': 'NON_RELEVANT',
            'relevance_explanation': 'All search results not relevant to chosen author '+author_choice,
            'model_used': model_choice,
            'prompt_tokens': 0,
            'completion_tokens': 0,
            'total_tokens': 0,
            'eval_prompt_tokens': 0,
            'eval_completion_tokens': 0,
            'eval_total_tokens': 0,
            'openai_cost': 0
        }    

    # limit to up to CONTEXT_NUM results
    reranked_results = reranked_results[:min(CONTEXT_NUM, len(reranked_results))]

    # simple options for user query rewriting to manage output length
    if response_length == 'S':
        max_length = 200
    elif response_length == 'M':
        max_length = 500
    else: # 'L'
        max_length = 1000

    prompt = build_prompt(query, category_choice, reranked_results, max_length)

    answer, tokens, response_time = llm(prompt, model_choice, max_length)
    
    relevance, explanation, eval_tokens = evaluate_relevance(query, answer)

    openai_cost = calculate_openai_cost(model_choice, tokens)
 
    return {
        'answer': answer,
        'response_time': response_time,
        'relevance': relevance,
        'relevance_explanation': explanation,
        'model_used': model_choice,
        'prompt_tokens': tokens['prompt_tokens'],
        'completion_tokens': tokens['completion_tokens'],
        'total_tokens': tokens['total_tokens'],
        'eval_prompt_tokens': eval_tokens['prompt_tokens'],
        'eval_completion_tokens': eval_tokens['completion_tokens'],
        'eval_total_tokens': eval_tokens['total_tokens'],
        'openai_cost': openai_cost
    }
