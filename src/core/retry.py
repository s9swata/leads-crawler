"""Retry decorator with exponential backoff for sync and async functions."""

import asyncio
import logging
import random
import time
from functools import wraps
from typing import Callable, Tuple, Type

from typing_extensions import ParamSpec

logger = logging.getLogger(__name__)

P = ParamSpec("P")


def retry(
    max_retries: int = 3,
    initial_backoff: float = 1.0,
    backoff_factor: float = 2.0,
    retry_on: Tuple[Type[Exception], ...] = (Exception,),
    include_jitter: bool = True,
):
    """
    Retry decorator with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        initial_backoff: Initial backoff duration in seconds (default: 1.0)
        backoff_factor: Multiplier for backoff on each retry (default: 2.0)
        retry_on: Tuple of exception types to retry on (default: all exceptions)
        include_jitter: Whether to add random jitter to backoff (default: True)

    Usage:
        @retry(max_retries=5, initial_backoff=1.0, backoff_factor=2.0)
        async def my_async_function():
            ...

        @retry(max_retries=3, retry_on=(httpx.HTTPError,))
        def my_sync_function():
            ...
    """

    def decorator(func: Callable[P, any]) -> Callable[P, any]:
        # Check if the function is async
        is_async = asyncio.iscoroutinefunction(func)

        if is_async:

            @wraps(func)
            async def async_wrapper(*args: P.args, **kwargs: P.kwargs):
                backoff = initial_backoff

                for attempt in range(max_retries + 1):
                    try:
                        return await func(*args, **kwargs)
                    except retry_on as e:
                        if attempt == max_retries:
                            logger.error(
                                f"Max retries ({max_retries}) reached for {func.__name__}"
                            )
                            raise

                        # Calculate backoff with optional jitter
                        jitter = (
                            random.uniform(0, 0.5 * backoff) if include_jitter else 0
                        )
                        sleep_duration = backoff + jitter

                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries + 1} failed for "
                            f"{func.__name__}: {e}. Retrying in {sleep_duration:.2f}s..."
                        )

                        await asyncio.sleep(sleep_duration)
                        backoff *= backoff_factor

                # Should not reach here, but just in case
                return await func(*args, **kwargs)

            return async_wrapper
        else:

            @wraps(func)
            def sync_wrapper(*args: P.args, **kwargs: P.kwargs):
                backoff = initial_backoff

                for attempt in range(max_retries + 1):
                    try:
                        return func(*args, **kwargs)
                    except retry_on as e:
                        if attempt == max_retries:
                            logger.error(
                                f"Max retries ({max_retries}) reached for {func.__name__}"
                            )
                            raise

                        # Calculate backoff with optional jitter
                        jitter = (
                            random.uniform(0, 0.5 * backoff) if include_jitter else 0
                        )
                        sleep_duration = backoff + jitter

                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries + 1} failed for "
                            f"{func.__name__}: {e}. Retrying in {sleep_duration:.2f}s..."
                        )

                        time.sleep(sleep_duration)
                        backoff *= backoff_factor

                # Should not reach here, but just in case
                return func(*args, **kwargs)

            return sync_wrapper

    return decorator
