#!/bin/bash

# Start Ollama in the background.
ollama serve &
# Record Process ID.
pid=$!

# Pause for Ollama to start.
sleep 5

echo
echo 'Pulling ollama phi3 model disabled by default, just uncomment the line below'
echo
# ollama pull phi3

echo
echo 'Pulling ollama phi3.5 model'
echo
ollama pull phi3.5

echo
echo 'Pulling ollama qwen2.5:3b model disabled by default, just uncomment the line below'
echo
# ollama pull qwen2.5:3b

echo
echo 'Pulling ollama llama3.2:3b model disabled by default, just uncomment the line below'
echo
# ollama pull llama3.2:3b


# Wait for Ollama process to finish.
wait $pid