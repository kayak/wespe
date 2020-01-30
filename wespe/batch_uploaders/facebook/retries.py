def should_retry_facebook_batch(facebook_batch) -> bool:
    """
    Returns True when all the failed requests, if any, are transient errors. Otherwise False.

    :return: a boolean.
    """
    return any(
        error.is_transient if error else False
        for error in facebook_batch.errors
    )
