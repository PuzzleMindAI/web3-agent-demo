from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field, field_validator, model_validator

from config.base import BaseConfig
from common.utils import check_address


class TokenMetadata(BaseModel):
    is_native: bool
    name: str
    symbol: str
    address: str
    decimals: int

    @field_validator("address", mode="before")
    @classmethod
    def check_address(cls, v: Any) -> Any:
        return check_address(v)


class ChainMetadata(BaseModel):
    chain_id: int
    name: str
    rpc_url: str


class ChainConfig(BaseConfig):
    chain: ChainMetadata
    """chain metadata"""
    tokens: List[TokenMetadata]
    """tokens: list of tokens on chain"""

    token_cache_by_symbol: Dict[str, TokenMetadata] = Field(default={}, exclude=True)  #: :meta private:
    token_cache_by_address: Dict[str, TokenMetadata] = Field(default={}, exclude=True)  #: :meta private:

    @model_validator(mode="after")
    @classmethod
    def validate_environment(cls, value: Any) -> Any:
        """Validate token list."""
        assert isinstance(value, ChainConfig)
        for token in value.tokens:
            value.token_cache_by_symbol[token.symbol] = token
            value.token_cache_by_address[token.address] = token
        return value

    def get_token(self, symbol: Optional[str], address: Optional[str]) -> TokenMetadata:
        if symbol is not None:
            if symbol in self.token_cache_by_symbol:
                return self.token_cache_by_symbol[symbol]
        if address is not None:
            if address in self.token_cache_by_address:
                return self.token_cache_by_address[address]

        if symbol is None and address is None:
            raise ValueError("Either symbol or address must be provided")
        else:
            raise ValueError(f"Token (symbol = {symbol}, address = {address}) not found in token list")
