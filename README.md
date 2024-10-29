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

- [Setup environment](#hammer_and_wrench-setup-environment)
- [Start the app](#arrow_forward-start-the-app)
- [Interact with the app](#speech_balloon-interact-with-the-app)
- [Monitoring](#bar_chart-monitoring)
- [Retrieval evaluation](#retrieval-evaluation)
- [Best practices](#best-practices)

### :hammer_and_wrench: Setup environment

1. **Fork this repo on GitHub**. Or use `git clone https://github.com/dmytrovoytko/llm-bookclub.git` command to clone it locally, then `cd llm-bookclub`.
2. Create GitHub CodeSpace from the repo ‼️ **use 4-core - 16GB RAM machine type**.
3. **Start CodeSpace**
4. **Go to the app directory** `cd ai_book_club`
5. The app works in docker containers, **you don't need to install packages locally to test it**.
6. Only if you want to develop the project locally, you can run `pip install -r requirements.txt` (project tested on python 3.11/3.12).
6. **If you want to use gpt-3.5/gpt-4 API you need to correct OPENAI_API_KEY in `.env` file**, which contains all configuration settings. 
7. By follwing default instructions (below), scripts will load Ollama/phi3.5 model for processing questions and evaluating results. If you want to use also Ollama/phi3, Ollama/qwen2.5:3b or Ollama/llama3.2:3b uncomment a line in `ollama_pull.sh`. Similarly you can load other Ollama models (you may need to adjust `app.py` for adding them to UI choices).

### :arrow_forward: Start the app

1. **Run `bash deploy.sh` to start all containers**, including elasticsearch, ollama, postgres, streamlit, grafana. It takes at least 5 minutes to download/build corresponding images, then get all services ready to serve. So you can make yourself some tea/coffee meanwhile. When new log messages stop appering, press enter to return to a command line.

![docker-compose up](/screenshots/docker-compose-00.png)

When you see these messages app is ready

![docker-compose up](/screenshots/docker-compose-01.png)

2. I put all init scripts to `start_app.sh` which starts automatically in `streamlit` container. Alternatively you can initialize ElasticSearch and PostgreSQL manually by running `bash init_db_es.sh` ("plan B" if something unexpected happens). 

* to ingest ...

![init_es](/screenshots/init_db_es-00.png)

... and index book reviews database:

![init_es](/screenshots/init_db_es-01.png)

* to create PostgreSQL tables:

![init_db](/screenshots/init_db_es-02.png)

* and create Grafana dashboard (monitoring). Alternatively you can run it manually: `bash init_gr.sh`

![Grafana init_gr](/screenshots/init_gr.png)

3. Default Ollama model (phi3.5) should be pulled automatically. Alternatively you can run `bash ollama_pull.sh` to pull it and other Ollama models:

![Ollama pull](/screenshots/ollama_pulled.png)

If you want to use other models, you can modify `ollama_pull.sh` script accordingly, then update `app.py` to add your model names.

4. Finally, open streamlit app: switch to ports tab and click on the link with port 8501 (🌐 icon).

![Ports streamlit open](/screenshots/streamlit-open.png)

### :speech_balloon: Interact with the app

1. Set query parameters - choose book category and author, then LLM model and query parameters (search type - text/vector/hybrid; response length - small, medium, long). Finally enter your question.

2. Press 'Find the answer' button, wait for the response. For Ollama phi3.5/qwen2.5 in CodeSpace response time was around a minute.

![streamlit Find the answer](/screenshots/streamlit-00.png)

3. RAG evaluation: check relevance evaluated by LLM (default model to use for this is defined in `.env` file).

![streamlit check](/screenshots/streamlit-01.png)

4. Give your feedback by pressing corresponding number of stars 🌟🌟🌟🌟🌟
- 1-2 are negative
- 4-5 are positive

![streamlit check](/screenshots/streamlit-02.png)

Both types of evaluation (from LLM and from user) are stored in the database and can be monitored.

5. App starts in the wide mode by default. You can switch it off in streamlit settings (upper right corner).

![streamlit check](/screenshots/streamlit-03.png)

### :bar_chart: Monitoring

You can monitor app performance in Grafana dashboard

1. As mentioned above, dashboard should be created automatically or by running script: `bash init_gr.sh`

2. To open Grafana switch to the PORTS tab (as with streamlit) and click on the link with port 3000 (🌐 icon). After loading Grafana use default credentials:
- Login: "admin"
- Password: "admin"

3. Click 'Dashboards' in the left pane and choose 'AI Book Club'.

![Grafana dasboard](/screenshots/grafana-00.png)

4. Check out app performance

![Grafana dasboard](/screenshots/grafana-01.png)

### :stop_sign: Stop all containers

Run `docker compose down` in command line to stop all running services.

Don't forget to remove downloaded images if you experimented with project locally! Use `docker images` to list all images and then `docker image rm ...` to remove those you don't need anymore.


## Retrieval evaluation

Notebooks with text only and vector search retrieval evaluation are in [evaluation](/evaluation) directory.

- experiment with weights and boost to improve retrieval metrics


## Best practices

 * [x] Hybrid search: combining both text and vector search (Elastic search, encoding)
 * [x] Reranking (extra filtering) and user query rewriting (simplified)


## Next steps

I plan to:
- add more book reviews to the dataset, add some more categories
- keep tuning prompts to improve retrieval quality

Stay tuned!

## Support

🙏 Thank you for your attention and time!

- If you experience any issue while following this instruction (or something left unclear), please add it to [Issues](/issues), I'll be glad to help/fix. And your feedback, questions & suggestions are welcome as well!
- Feel free to fork and submit pull requests.

If you find this project helpful, please ⭐️star⭐️ my repo 
https://github.com/dmytrovoytko/llm-bookclub to help other people discover it 🙏

Made with ❤️ in Ukraine 🇺🇦 Dmytro Voytko
