from typing import Any
from eth_utils import is_address


def check_address(v: Any) -> Any:
    if is_address(v):
        return v
    else:
        raise ValueError(f"Invalid address {v}")
