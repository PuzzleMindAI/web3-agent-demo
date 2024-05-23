import asyncio
import logging
import sys
import uvicorn
import argparse
import nest_asyncio

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain.globals import set_debug, set_verbose
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_openai.chat_models import ChatOpenAI
from langchain_experimental.tools import PythonAstREPLTool
from web3 import AsyncWeb3


def parse_args():
    parser = argparse.ArgumentParser(prog="web3-agent", description="Run the web3 agent service.")
    parser.add_argument(
        "--log-level", type=str, default="INFO", help="log level"
    )
    parser.add_argument(
        "--debug-mode", type=bool, default=False, help="debug mode"
    )
    parser.add_argument(
        "--verbose-mode", type=bool, default=False, help="verbose mode"
    )
    parser.add_argument(
        "--host", type=str, default="0.0.0.0", help="host address"
    )
    parser.add_argument(
        "--port", type=int, default=8901, help="port number"
    )
    parser.add_argument(
        "--model-config", type=str, default=".config/model.json", help="model config file path"
    )
    parser.add_argument(
        "--chain-config", type=str, default=".config/chain.json", help="chain config file path"
    )

    return parser.parse_args()


async def main():
    args = parse_args()

    root_path = Path(__file__).parent.parent.as_posix()
    sys.path.append(root_path)

    from executors.chatter import Chatter
    from executors.api import register_agent_api
    from functions.token.balance import BalanceGetter
    from functions.defillama.tvl import TVLQuerier
    from functions.defillama.yielding import YieldQuerier
    from config import ChainConfig, ModelConfig

    model_config = ModelConfig.from_file(Path(args.model_config))
    chain_config = ChainConfig.from_file(Path(args.chain_config))

    # setup logging
    logging.basicConfig(
        level=logging.getLevelName(args.log_level),
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    set_debug(args.debug_mode)
    set_verbose(args.verbose_mode)

    web3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(chain_config.chain.rpc_url))
    balance_getter = BalanceGetter(
        chain_config=chain_config,
        async_web3=web3,
    )
    tvl_querier = TVLQuerier()
    yield_querier = YieldQuerier()
    # routing_querier = RoutingQuerier(
    #     chain_config=chain_config,
    #     base_url="https://routing-prod.web3.com/quote",
    # )
    python_tool = PythonAstREPLTool(
        metadata={"notification": "\n*Running Python code...*\n"},
    )
    tavily_tool = TavilySearchResults(
        metadata={"notification": "\n*Searching data on Tavily Search Engine...*\n"},
    )

    agent_model = ChatOpenAI(**model_config.agent_args.model_dump())
    chatter = Chatter(
        model=agent_model,
        tools=[
            balance_getter.tool(),
            tvl_querier.tool(),
            yield_querier.tool(),
            # routing_querier.tool(),
            python_tool,
            tavily_tool,
        ],
    )

    # setup service
    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    app.include_router(register_agent_api(chatter))

    # run app
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.run(main())
