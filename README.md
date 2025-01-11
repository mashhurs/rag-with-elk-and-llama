# What is this repo?
_Note: this tutorial is an education purpose only_

# References
- For kNN search see https://www.elastic.co/search-labs/tutorials/search-tutorial/welcome

# Prerequisites
1) Setup local LLama
  - Install Ollama: `curl -fsSL https://ollama.com/install.sh | sh`
  - Run Ollama3: `ollama run llama3`
  - Reference: https://github.com/ollama/ollama
2) Setup local Elasticsearch
  - Clone https://github.com/elastic/start-local.git
  - Run `./start-local.sh`
  - Write down credentials (will need to store in `.env` of the Flask application)
3) Generate embeddings with Logstash
  For ingesting data and generate embeddings, use Logstash with [`embeddings_generator` plugin](https://github.com/mashhurs/logstash-filter-embeddings_generator)
  Your pipeline may look like this:
    ```shell
    input {
      file {
        path => "/path-to/*/*.txt"
        mode => "read"
        start_position => "beginning"
        ecs_compatibility => "disabled"
      }
    }
    
    filter {
        mutate {
            remove_field => "[event][original]"
        }
        embeddings_generator {
            source => "[message]"
            target => "embedding"
            # `path` cane be local model, remote full path or base (example: huggingface pytorch) URL
            #  `path` examples
            #   path => "djl://ai.djl.huggingface.pytorch"
            #   model_name => "BAAI/bge-small-en-v1.5"                    # dimension 384
            #   model_name => "sentence-transformers/all-MiniLM-L6-v2"    # dimension 384
            #   model_name => "Trelis/all-MiniLM-L12-v2-ft-Llama-3-70B"   # DJL doesn't support by default, need conversion
            #   model_name => "eeeyounglee/EEVE-10.8B-mean-4096-4"        # DJL doesn't support by default, need conversion
            #   downloaded EEVE-10.8B-mean-4096-4 from huggingface and converted into torchscript format
            #   point to local model
            path => "/path-to-local/model/EEVE-10.8B-mean-4096-4"
         }
    }
    
    output {
        elasticsearch {
           ecs_compatibility => "disabled"
           user => "{username}"
           password => "{pwd}"
           index => "{index-to-store-data-and-embeddings}"
        }
    }
    ```

## Run frontend (current flask) application
- Setup
    ```shell
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```
- Rename `.env_example` to `.env` and replace variables with your own
- Run:
    ```shell
    flask run
    ```

