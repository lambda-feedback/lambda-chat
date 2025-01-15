# Lambda Feedback Chatbot

This repository contains the code needed to run a modular chat functionality that provides multiple chatbot API endpoints [written in Python].

## Quickstart

This chapter helps you to quickly set up a new Python chat module function using this repository.

> [!NOTE]
> To develop this function further, you will require the following environment variables in your `.env` file:
```bash
> If you use azure-openai:
AZURE_OPENAI_API_KEY
AZURE_OPENAI_ENDPOINT
AZURE_OPENAI_API_VERSION
AZURE_OPENAI_CHAT_DEPLOYMENT_NAME
AZURE_OPENAI_EMBEDDING_3072_DEPLOYMENT
AZURE_OPENAI_EMBEDDING_1536_DEPLOYMENT
AZURE_OPENAI_EMBEDDING_3072_MODEL
AZURE_OPENAI_EMBEDDING_1536_MODEL

> If you use openai:
OPENAI_API_KEY
OPENAI_MODEL

> For monitoring of the LLM calls (follow instructions on how to set up on langsmith):
LANGCHAIN_TRACING_V2
LANGCHAIN_ENDPOINT
LANGCHAIN_API_KEY
LANGCHAIN_PROJECT
```

#### 1. Clone the repository

Clone this repository to your local machine using the following command:

```bash
git clone https://github.com/lambda-feedback/lambda-chat
```

#### 2. Develop the chat function

You're ready to start developing your chat function. Head over to the [Development](#development) section to learn more.

#### 3. Update the README

In the `README.md` file, change the title and description so it fits the purpose of your chat function.

Also, don't forget to update or delete the Quickstart chapter from the `README.md` file after you've completed these steps.

## Development

You can create your own invocation to your own agents hosted anywhere. Copy the `base_agent` from `src/agents/` and edit it to match your LLM agent requirements. Import the new invocation in the `module.py` file.

You agent can be based on an LLM hosted anywhere, you have available currently OpenAI, AzureOpenAI, and Ollama models but you can introduce your own API call in the `src/agents/llm_factory.py`.

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Python](https://www.python.org)

### Repository Structure

```bash
.github/workflows/
    dev.yml                           # deploys the DEV function to Lambda Feedback
    main.yml                          # deploys the STAGING function to Lambda Feedback
    test-report.yml                   # gathers Pytest Report of function tests

src/module.py       # chat_module function implementation
src/module_test.py  # chat_module function tests
src/agents/         # find all agents developed for the chat functionality
src/agents/utils/test_prompts.py      # allows testing of any LLM agent on a couple of example inputs containing Lambda Feedback Questions and synthetic student conversations
```

## Run the Chat Script

You can run the Python function itself. Make sure to have a main function in either `src/module.py` or `index.py`.

```bash
python src/module.py
```

You can also use the `testbench_agents.py` script to test the agents with example inputs from Lambda Feedback questions and synthetic conversations.
```bash
python src/agents/utils/testbench_agents.py
```

### Building the Docker Image

To build the Docker image, run the following command:

```bash
docker build -t llm_chat .
```

### Running the Docker Image

To run the Docker image, use the following command:

#### Without .env file:

```bash
docker run -e OPENAI_API_KEY={your key} -e OPENAI_MODEL={your LLM chosen model name} -p 8080:8080 llm_chat
```

#### With container name (for interaction, e.g. copying file from inside the docker container):

```bash
docker run --env-file .env -it --name my-lambda-container -p 8080:8080 llm_chat
```

This will start the evaluation function and expose it on port `8080` and it will be open to be curl:

```bash
curl --location 'http://localhost:8080/2015-03-31/functions/function/invocations' --header 'Content-Type: application/json' --data '{"message":"hi","params":{"conversation_id":"12345Test","conversation_history": [{"type":"user","content":"hi"}]}}'
```

### Call Docker Container From Postman

POST URL:

```bash
http://localhost:8080/2015-03-31/functions/function/invocations
```

Body:

```JSON
{
    "message":"hi",
    "params":{
        "conversation_id":"12345Test",
        "conversation_history": [{"type":"user","content":"hi"}]
    }
}
```

Body with optional Params:
```JSON
{
    "message":"hi",
    "params":{
        "conversation_id":"12345Test",
        "conversation_history":[{"type":"user","content":"hi"}],
        "summary":" ",
        "conversational_style":" ",
        "question_response_details": "",
        "include_test_data": true,
        "agent_type": {agent_name}
    }
}
```

### Deploy to Lambda Feedback

Deploying the chat function to Lambda Feedback is simple and straightforward, as long as the repository is within the [Lambda Feedback organization](https://github.com/lambda-feedback).

After configuring the repository, a [GitHub Actions workflow](.github/workflows/main.yml) will automatically build and deploy the evaluation function to Lambda Feedback as soon as changes are pushed to the main branch of the repository. For development, the [GitHub Actions Dev workflow](.github/workflows/dev.yml) also deploys a dev version of the function onto AWS.

## Troubleshooting

### Containerized Function Fails to Start

If your evaluation function is working fine when run locally, but not when containerized, there is much more to consider. Here are some common issues and solution approaches:

**Run-time dependencies**

Make sure that all run-time dependencies are installed in the Docker image.

- Python packages: Make sure to add the dependency to the `requirements.txt` or `pyproject.toml` file, and run `pip install -r requirements.txt` or `poetry install` in the Dockerfile.
- System packages: If you need to install system packages, add the installation command to the Dockerfile.
- ML models: If your evaluation function depends on ML models, make sure to include them in the Docker image.
- Data files: If your evaluation function depends on data files, make sure to include them in the Docker image.
