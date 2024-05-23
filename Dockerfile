FROM condaforge/mambaforge

LABEL authors="Lone"

WORKDIR /web3agent

COPY . /web3agent

RUN mamba env create -f /web3agent/environment.yml

EXPOSE 8901

ENV OPENAI_API_KEY="xxx" \
    TAVILY_API_KEY="xxx"

ENTRYPOINT [ \
    "conda", "run", "--no-capture-output", "-n", "web3agent", \
    "python", "/web3agent/app/run_svc.py", "--host=127.0.0.1", "--port=8901", \
    "--model-config=/web3agent/.config/model.json", "--chain-config=/web3agent/.config/chain.json"  \
]
