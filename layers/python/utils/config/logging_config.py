import logging

def configure_logging():
    """Configura los niveles de logging para diferentes módulos."""
    # Configurar loggers de AWS
    logging.getLogger('botocore').setLevel(logging.WARNING)
    logging.getLogger('boto3').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    # Desactivar propagación de logs específicos
    logging.getLogger('botocore.credentials').propagate = False