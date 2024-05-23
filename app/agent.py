from pathlib import Path
from langchain_community.tools.render import format_tool_to_openai_function

from functions.swap.uniswap_v3.routing_query import RoutingQuerier
from config import ChainConfig


if __name__ == "__main__":
    chain_config = ChainConfig.from_file(Path("../.config/chain.json"))
    agent = RoutingQuerier(chain_config=chain_config, base_url="https://routing-api.0x.org/swap/v1/quote")
    tool = agent.tool()
    description = format_tool_to_openai_function(tool)
    print(description)
