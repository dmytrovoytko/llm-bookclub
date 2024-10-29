# LLM project AI 📚 Book Club

Pet project / 3rd Capstone project for DataTalks.Club LLM ZoomCamp`24: 

RAG application based on best selling book reviews.

![LLM project AI Book Club](/screenshots/llm-bookclub.png)

Project can be tested and deployed in **GitHub CodeSpaces** (the easiest option, and free), cloud virtual machine (AWS, Azure, GCP), or just locally with/without GPU! Works with Ollama and ChatGPT.

For GitHub CodeSpace option you don't need to use anything extra at all - just your favorite web browser + GitHub account is totally enough.


## Problem statement

Do you read books? Then you probably know how challenging sometimes can be the process of choosing your next book. Even when when we have all those "Bestsellers lists", best selling doesn't mean it's a right book for you personally...

📖 



## 🎯 Goals

This is my 3rd LLM project started during [LLM ZoomCamp](https://github.com/DataTalksClub/llm-zoomcamp)'24.

LLM project AI 📖 Book Club should assist users in choosing next book to read and getting insights from other readers. It should provide a chatbot-like interface to easily find answers based on book reviews without scrolling through Amazon pages.

Thanks to LLM ZoomCamp for the reason to keep learning new cool tools! 


## 🔢 Dataset

I parsed bestsellers collections in 4 categories and then used ETL scripts from my previous [Data Engineering project Amazon Reviews](https://github.com/dmytrovoytko/data-engineering-amazon-reviews) to extract the most helpful reviews from [Amazon Reviews'23` dataset](https://amazon-reviews-2023.github.io/). 


## :toolbox: Tech stack

* Frontend: 
    - UI: Streamlit web application for conversational interface
    - Monitoring: Grafana
* Backend:
    - Python 3.11/3.12
    - Docker and docker-compose for containerization
    - Elastic search to index interview questions-answers bank
    - OpenAI-compatible API, that supports working with Ollama locally, even without GPU
        * you can make it working fast - with your own OPENAI_API_KEY - choose gpt-3.5/gpt-4o
        * alternatively you can pull and test any model from [Ollama library](https://ollama.com/library)
        * Ollama tested with Microsoft Phi 3/3.5 and Alibaba qwen2.5:3b models, surprisingly their responses often were more relevant than Llama3.2
    - PostgreSQL to store asked questions & answers, evaluation (relevance) and user feedback

## 🚀 Instructions to reproduce
