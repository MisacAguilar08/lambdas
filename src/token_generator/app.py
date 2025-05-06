import os
import json
import jwt
from datetime import datetime, timedelta
from typing import Dict, Any

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Genera un token JWT para autenticación
    """
    try:
        # Obtener el cuerpo de la solicitud
        body = json.loads(event.get('body', '{}'))
        
        # Validar que se proporcione un user_id
        user_id = body.get('user_id')
        if not user_id:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'user_id es requerido'
                })
            }
        
        # Configurar los claims del token
        now = datetime.utcnow()
        payload = {
            'sub': user_id,  # subject (usuario)
            'iat': now,      # issued at (fecha de emisión)
            'exp': now + timedelta(hours=24),  # expiration (24 horas)
            'iss': 'lambda-api'  # issuer (emisor)
        }
        
        # Generar el token
        secret = os.environ.get('AUTH_TOKEN_SECRET')
        token = jwt.encode(payload, secret, algorithm='HS256')
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'token': token,
                'expires_in': 86400,  # 24 horas en segundos
                'token_type': 'Bearer'
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }