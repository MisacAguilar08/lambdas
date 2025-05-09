from aws_lambda_powertools import Logger
from functools import lru_cache

@lru_cache
def get_logger(service_name: str = "payment-service") -> Logger:
    """
    Returns a singleton instance of the Logger.
    
    Args:
        service_name (str): The name of the service using the logger.
                          Defaults to "payment-service"
    
    Returns:
        Logger: Configured Logger instance from aws_lambda_powertools
    """
    return Logger(
        service=service_name,
        sample_rate=1,
        persistence_store=None
    )