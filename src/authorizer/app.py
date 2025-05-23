import os
import jwt
from typing import Dict, Any
from utils.ssm.parameter import get_parameter

def generate_policy(principal_id: str, effect: str, resource: str) -> Dict[str, Any]:
    """
    Genera una política IAM para API Gateway basada en el resultado de la autenticación
    """
    return {
        'principalId': principal_id,
        'policyDocument': {
            'Version': '2012-10-17',
            'Statement': [
                {
                    'Action': 'execute-api:Invoke',
                    'Effect': effect,
                    'Resource': resource
                }
            ]
        }
    }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Custom Authorizer para API Gateway que valida tokens JWT
    """
    try:
        # Obtener el token del header Authorization
        auth_header = event.get('authorizationToken', '')
        if not auth_header.startswith('Bearer '):
            raise Exception('Format is Authorization: Bearer [token]')
        
        token = auth_header.split(' ')[1]
        
        # Validar el token
        secret = os.environ.get('AUTH_TOKEN_SECRET')
        token_time = get_parameter(os.environ['SSM_TOKEN_TIME_PATH'])
        decoded = jwt.decode(token, secret, algorithms=['HS256'])
        
        # Verificar que sea un access_token
        if decoded.get('type') != 'access':
            raise Exception('Token tipo inválido - Se requiere access_token')
        
        # Si la validación es exitosa, permitir el acceso
        return generate_policy(
            decoded['sub'],
            'Allow',
            event['methodArn']
        )
        
    except Exception as e:
        # Si hay algún error, denegar el acceso
        return generate_policy(
            'user',
            'Deny',
            event['methodArn']
        )