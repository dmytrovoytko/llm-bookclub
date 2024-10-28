#!/bin/bash
echo
echo '1. STARTING DATABASE, ELASTICSEARCH AND GRAFANA INIT SCRIPTS'
echo

echo '1.1. ELASTICSEARCH INDEXING'
export USE_ELASTIC=true
# until [ $(curl -u elastic https://localhost:9200/_cluster/health | grep -c green) -eq 1 ]; do
#   sleep 2
# done &

INDEX_NAME=book-reviews
# status=$(curl -I -XHEAD 'localhost:9200/$INDEX_NAME?test')
# echo "ELASTICSEARCH Index exist? "$status
python ingest.py

echo
echo '1.2. POSTGRES DB INIT'
python db_prep.py

echo
echo '1.3. GRAFANA DASHBOARD INIT'
python init_gr.py

echo
echo '2. Starting Streamlit app...'
echo
streamlit run app.py

sleep 5

