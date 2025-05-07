import boto3
import json
from typing import Any

def get_parameter(parameter_name: str) -> Any:
    """
    Obtiene un parámetro de AWS Systems Manager Parameter Store
    """
    ssm = boto3.client('ssm')
    try:
        response = ssm.get_parameter(Name=parameter_name)
        return response['Parameter']['Value']
    except Exception as e:
        raise Exception(f"Error al obtener el parámetro {parameter_name}: {str(e)}")