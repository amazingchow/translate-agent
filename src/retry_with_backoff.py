import functools
import random
import time


class MaximumNumberOfRetriesExceededError(Exception):
    def __init__(self, message, errors=None):
        super().__init__(message)
        self.errors = errors


def retry_with_exponential_backoff(
    *,
    initial_delay: float = 1,
    exponential_base: float = 2,
    jitter: bool = True,
    max_retries: int = 2,
    errors: tuple = (Exception,),
):
    """Retry a function with exponential backoff."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if max_retries > 10:
                raise ValueError("Max retries should be less than 10.")
            # Initialize variables
            num_retries = 0
            delay = initial_delay
            # Loop until a successful response or max_retries is hit or an exception is raised
            while 1:
                try:
                    return func(*args, **kwargs)
                # Retry on specified errors
                except errors as exc:
                    print(f"caught error: {exc}, num_retries: {num_retries}.")
                    # Increment retries
                    num_retries += 1
                    # Check if max retries has been reached
                    if num_retries > max_retries:
                        raise MaximumNumberOfRetriesExceededError(
                            f"Maximum number of retries ({max_retries}) exceeded."
                        )
                    # Compute the delay
                    delay = initial_delay * (exponential_base**num_retries) * (1 + jitter * random.random())
                    # Sleep for the delay
                    print(f"create (backoff): sleeping for {delay} seconds.")
                    time.sleep(delay)
                # Raise exceptions for any errors not specified
                except Exception as exc:
                    raise exc

        return wrapper

    return decorator


def retry_with_constant_backoff(
    *,
    constant_delay: float = 1,
    jitter: bool = True,
    max_retries: int = 2,
    errors: tuple = (Exception,),
):
    """Retry a function with constant backoff."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if max_retries > 10:
                raise ValueError("Max retries should be less than 10.")
            # Initialize variables
            num_retries = 0
            # Loop until a successful response or max_retries is hit or an exception is raised
            while 1:
                try:
                    return func(*args, **kwargs)
                # Retry on specified errors
                except errors as exc:
                    print(f"caught error: {exc}, num_retries: {num_retries}.")
                    # Increment retries
                    num_retries += 1
                    # Check if max retries has been reached
                    if num_retries > max_retries:
                        raise MaximumNumberOfRetriesExceededError(
                            f"Maximum number of retries ({max_retries}) exceeded."
                        )
                    # Compute the delay
                    delay = constant_delay * (1 + jitter * random.random())
                    # Sleep for the delay
                    print(f"create (backoff): sleeping for {delay} seconds.")
                    time.sleep(delay)
                # Raise exceptions for any errors not specified
                except Exception as exc:
                    raise exc

        return wrapper

    return decorator
