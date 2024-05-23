from typing import Any, Optional, LiteralString, Callable, Awaitable
from pydantic.v1 import BaseModel, Field, validator
from web3 import Web3, AsyncWeb3
from web3.types import ABI
from web3.utils.address import to_checksum_address

from config.chain import ChainConfig
from common.utils import check_address
from functions.wrapper import FunctionWrapper


class BalanceArgs(BaseModel):
    account: str = Field(description="The account address to query balance for")
    token_symbol: Optional[str] = Field(None, description="The symbol of the token")
    token_address: Optional[str] = Field(None, description="The contract address of the token")

    @validator("account", pre=True)
    @classmethod
    def check_account(cls, v: Any) -> Any:
        return check_address(v)

    @validator("token_address", pre=True)
    @classmethod
    def check_token_contract(cls, v: Any) -> Any:
        if v is not None:
            return check_address(v)


class BalanceResult(BaseModel):
    balance: float = Field(description="The balance of the account")


class BalanceGetter(FunctionWrapper[BalanceArgs, BalanceResult]):
    chain_config: ChainConfig
    web3: Optional[Web3]
    async_web3: Optional[AsyncWeb3]

    abi: ABI = [
        {
            "inputs": [{"name": "account", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        }
    ]

    def __init__(
        self,
        *,
        chain_config: ChainConfig,
        web3: Optional[Web3] = None,
        async_web3: Optional[AsyncWeb3] = None,
    ):
        if not web3 and not async_web3:
            raise ValueError("Either web3 or async_web3 must be provided")
        self.chain_config = chain_config
        self.web3 = web3
        self.async_web3 = async_web3

        super().__init__()

    @classmethod
    def name(cls) -> LiteralString:
        return "balance_of"

    @classmethod
    def description(cls) -> LiteralString:
        return "useful for when you query token balance"

    @classmethod
    def notification(cls) -> str:
        return "\n*Querying token balance...*\n"

    @property
    def func(self) -> Optional[Callable[..., BalanceResult]]:
        if self.web3:
            def _balance_of(
                account: str,
                token_symbol: Optional[str] = None,
                token_address: Optional[str] = None,
            ) -> BalanceResult:
                assert self.web3 is not None

                token = self.chain_config.get_token(token_symbol, token_address)
                account = to_checksum_address(account)
                if token.is_native:
                    # native coin balance
                    balance = self.web3.eth.get_balance(account)
                else:
                    # ERC20 token balance
                    contract = self.web3.eth.contract(
                        address=to_checksum_address(token.address),
                        abi=self.abi,
                    )
                    balance = contract.functions.balanceOf(account).call()
                return BalanceResult(balance=balance / (10 ** token.decimals))

            return _balance_of
        else:
            return None

    @property
    def async_func(self) -> Optional[Callable[..., Awaitable[BalanceResult]]]:
        if self.async_web3:
            async def _balance_of(
                account: str,
                token_symbol: Optional[str] = None,
                token_address: Optional[str] = None,
            ) -> BalanceResult:
                assert self.async_web3 is not None
                token = self.chain_config.get_token(token_symbol, token_address)
                account = to_checksum_address(account)
                if token.is_native:
                    # native coin balance
                    balance = await self.async_web3.eth.get_balance(account)
                else:
                    # ERC20 token balance
                    contract = self.async_web3.eth.contract(
                        address=to_checksum_address(token.address),
                        abi=self.abi,
                    )
                    balance = await contract.functions.balanceOf(account).call()
                return BalanceResult(balance=balance / (10 ** token.decimals))

            return _balance_of
        else:
            return None
