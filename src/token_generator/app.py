
import os
import json
import jwt
from utils.ssm.parameter import get_parameter
from datetime import datetime, timedelta
from typing import Dict, Any

def generate_tokens(user_id: str) -> Dict[str, str]:
    """
    Genera access_token y refresh_token para un usuario
    """
    now = datetime.utcnow()

    # Configurar claims para access_token (corta duración - 1 hora)
    access_payload = {
        'sub': user_id,
        'iat': now,
        'exp': now + timedelta(hours=1),  # 1 hora de validez
        'iss': 'lambda-api',
        'type': 'access'
    }

    # Configurar claims para refresh_token (larga duración - 7 días)
    refresh_payload = {
        'sub': user_id,
        'iat': now,
        'exp': now + timedelta(days=7),  # 7 días de validez
        'iss': 'lambda-api',
        'type': 'refresh'
    }

    secret = os.environ.get('AUTH_TOKEN_SECRET')

    # Generar ambos tokens
    access_token = jwt.encode(access_payload, secret, algorithm='HS256')
    refresh_token = jwt.encode(refresh_payload, secret, algorithm='HS256')

    return {
        'access_token': access_token,
        'refresh_token': refresh_token
    }

def refresh_access_token(refresh_token: str) -> Dict[str, str]:
    """
    Genera un nuevo access_token usando un refresh_token válido
    """
    secret = os.environ.get('AUTH_TOKEN_SECRET')
    try:
        # Decodificar y validar el refresh_token
        decoded = jwt.decode(refresh_token, secret, algorithms=['HS256'])

        # Verificar que sea un refresh_token
        if decoded.get('type') != 'refresh':
            raise ValueError('Token tipo inválido')

        # Generar nuevo access_token
        user_id = decoded['sub']
        now = datetime.utcnow()
        access_payload = {
            'sub': user_id,
            'iat': now,
            'exp': now + timedelta(hours=1),
            'iss': 'lambda-api',
            'type': 'access'
        }

        new_access_token = jwt.encode(access_payload, secret, algorithm='HS256')
        return {'access_token': new_access_token}

    except jwt.ExpiredSignatureError:
        raise ValueError('Refresh token expirado')
    except jwt.InvalidTokenError:
        raise ValueError('Refresh token inválido')

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Genera tokens JWT para autenticación o refresca access_token
    """
    try:
        token_time = get_parameter('/auth/token/time')
        print("Tiempo del token:"+token_time)
        body = json.loads(event.get('body', '{}'))

        # Ruta para generar nuevos tokens
        if body.get('grant_type') == 'password':
            user_id = body.get('user_id')
            if not user_id:
                return {
                    'statusCode': 400,
                    'body': json.dumps({
                        'error': 'user_id es requerido'
                    })
                }

            tokens = generate_tokens(user_id)
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'access_token': tokens['access_token'],
                    'refresh_token': tokens['refresh_token'],
                    'expires_in': 3600,  # 1 hora en segundos
                    'token_type': 'Bearer'
                })
            }

        # Ruta para refrescar access_token
        elif body.get('grant_type') == 'refresh_token':
            refresh_token = body.get('refresh_token')
            if not refresh_token:
                return {
                    'statusCode': 400,
                    'body': json.dumps({
                        'error': 'refresh_token es requerido'
                    })
                }

            try:
                new_tokens = refresh_access_token(refresh_token)
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'access_token': new_tokens['access_token'],
                        'expires_in': 3600,
                        'token_type': 'Bearer'
                    })
                }
            except ValueError as e:
                return {
                    'statusCode': 401,
                    'body': json.dumps({
                        'error': str(e)
                    })
                }

        else:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'grant_type inválido'
                })
            }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }