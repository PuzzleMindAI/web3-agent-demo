import httpx

from httpx import AsyncClient, Response
from typing import Any, Union, Literal, LiteralString, Optional, Callable, Awaitable
from pydantic.v1 import BaseModel, Field, validator

from functions.wrapper import FunctionWrapper
from common.utils import check_address
from config.chain import ChainConfig


class RoutingQueryArgs(BaseModel):
    amount_in: float = Field(description="Amount of the token to swap in")
    tp: Union[Literal["exactIn"], Literal["exactOut"]] = Field(description="Type of the swap event")
    recipient: str = Field(description="Recipient address of the token out")
    token_in_symbol: Optional[str] = Field(None, description="Symbol of the token to swap in")
    token_in_address: Optional[str] = Field(None, description="Contract address of the token to swap in")
    token_out_symbol: Optional[str] = Field(None, description="Symbol of the token to swap out")
    token_out_address: Optional[str] = Field(None, description="Contract address of the token to swap out")
    protocol: str = Field("v3", description="Protocol to use")
    enable_universal_router: bool = Field(False, description="Enable universal router")

    @validator("token_in_address", pre=True)
    @classmethod
    def check_token_in_address(cls, v: Any) -> Any:
        if v is not None:
            return check_address(v)

    @validator("token_out_address", pre=True)
    @classmethod
    def check_token_out_address(cls, v: Any) -> Any:
        if v is not None:
            return check_address(v)

    @validator("recipient", pre=True)
    @classmethod
    def check_recipient(cls, v: Any) -> Any:
        return check_address(v)


class RoutingResult(BaseModel):
    block_number: int = Field(description="Block number of the routing query simulated at")
    simulation_status: str = Field(description="Simulation status")
    simulation_error: bool = Field(description="Simulation error")
    gas_estimate_usd: float = Field(description="Gas estimated in USD for the swap transaction")
    routing: str = Field(description="Routing query string")
    amount_in: float = Field(description="Amount of the token to swap in")
    amount_out: float = Field(description="Amount of the token to swap out")


class RoutingQuerier(FunctionWrapper[RoutingQueryArgs, RoutingResult]):
    """Query routing information from the routing service."""

    chain_config: ChainConfig
    base_url: str

    def __init__(self, *, chain_config: ChainConfig, base_url: str):
        self.chain_config = chain_config
        self.base_url = base_url

        super().__init__()

    @classmethod
    def name(cls) -> LiteralString:
        return "routing_querier"

    @classmethod
    def description(cls) -> LiteralString:
        return "useful for when query the routing simulation for token swap on web3 platform"

    @classmethod
    def notification(cls) -> str:
        return "\n*Query routing simulation on web3 platform...*\n"

    def _create_params(
        self,
        amount_in: float,
        tp: Union[Literal["exactIn"], Literal["exactOut"]],
        recipient: str,
        token_in_symbol: Optional[str] = None,
        token_in_address: Optional[str] = None,
        token_out_symbol: Optional[str] = None,
        token_out_address: Optional[str] = None,
        protocol: str = "v3",
        enable_universal_router: bool = False,
    ) -> dict:
        token_in = self.chain_config.get_token(token_in_symbol, token_in_address)
        token_out = self.chain_config.get_token(token_out_symbol, token_out_address)
        return {
            "tokenInChainId": self.chain_config.chain.chain_id,
            "tokenInAddress": token_in.address,
            "tokenOutChainId": self.chain_config.chain.chain_id,
            "tokenOutAddress": token_out.address,
            "amount": int(amount_in * 10 ** token_in.decimals),
            "type": tp,
            "recipient": recipient,
            "protocols": protocol,
            "enableUniversalRouter": enable_universal_router,
        }

    @staticmethod
    def _create_result(resp: Response) -> RoutingResult:
        if resp.status_code == 200:
            body: dict = resp.json()
            return RoutingResult(
                block_number=int(body["blockNumber"]),
                simulation_status=body["simulationStatus"],
                simulation_error=body["simulationError"],
                gas_estimate_usd=float(body["gasUseEstimateUSD"]),
                routing=body["routeString"],
                amount_in=float(body["amountDecimals"]),
                amount_out=float(body["quoteDecimals"]),
            )
        else:
            raise RuntimeError(f"failed to query routing: status: {resp.status_code}, response: {resp.text}")

    @property
    def func(self) -> Optional[Callable[..., RoutingResult]]:
        def _query_routing(
            amount_in: float,
            tp: Union[Literal["exactIn"], Literal["exactOut"]],
            recipient: str,
            token_in_symbol: Optional[str] = None,
            token_in_address: Optional[str] = None,
            token_out_symbol: Optional[str] = None,
            token_out_address: Optional[str] = None,
            protocol: str = "v3",
            enable_universal_router: bool = False,
        ) -> RoutingResult:
            """Query routing information from the routing service."""
            resp = httpx.get(
                self.base_url,
                params=self._create_params(
                    amount_in,
                    tp,
                    recipient,
                    token_in_symbol,
                    token_in_address,
                    token_out_symbol,
                    token_out_address,
                    protocol,
                    enable_universal_router,
                ),
            )
            return self._create_result(resp)

        return _query_routing

    @property
    def async_func(self) -> Optional[Callable[..., Awaitable[RoutingResult]]]:
        async def _query_routing(
            amount_in: float,
            tp: Union[Literal["exactIn"], Literal["exactOut"]],
            recipient: str,
            token_in_symbol: Optional[str] = None,
            token_in_address: Optional[str] = None,
            token_out_symbol: Optional[str] = None,
            token_out_address: Optional[str] = None,
            protocol: str = "v3",
            enable_universal_router: bool = False,
        ) -> RoutingResult:
            """Query routing information from the routing service."""
            async with AsyncClient() as client:
                resp = await client.get(
                    self.base_url,
                    params=self._create_params(
                        amount_in,
                        tp,
                        recipient,
                        token_in_symbol,
                        token_in_address,
                        token_out_symbol,
                        token_out_address,
                        protocol,
                        enable_universal_router,
                    ),
                )
                return self._create_result(resp)

        return _query_routing
