#!/bin/bash
echo
echo '1. COPYING LATEST DATASET AND SCRIPTS'
echo
cp -r ../data .
# cp test.env .env

if [[ -e ".env" ]]
  then
    # loading script parameters from .env
    set -a            
    source .env
    set +a
else
    echo "No .env file with paramaters found. Exiting."
    exit 1
fi

echo
echo '2. Executing db_prep.py'
echo
docker exec -it streamlit python db_prep.py

echo
echo '3. Executing ingest.py'
echo
export USE_ELASTIC=true
docker exec -it streamlit python ingest.py

sleep 5
