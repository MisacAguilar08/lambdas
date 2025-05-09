import json
from aws_lambda_powertools.utilities.typing import LambdaContext
from utils.services.payment_service import PaymentService
from utils.logger import get_logger

logger = get_logger("payment_handler")
payment_service = PaymentService()

@logger.inject_lambda_context
async def lambda_handler(event: dict, context: LambdaContext) -> dict:
    """
    Handler para el registro de pagos.
    Delega toda la lógica de negocio al PaymentService.
    """
    try:
        # Extraer datos del evento
        body = json.loads(event.get('body', '{}'))
        
        # Enriquecer con datos del contexto
        body['source'] = 'api'
        if event.get('requestContext', {}).get('identity'):
            identity = event['requestContext']['identity']
            body['ip_address'] = identity.get('sourceIp')
            body['user_agent'] = identity.get('userAgent')
        
        # Delegar al servicio
        result = await payment_service.register_payment(body)
        
        # Mapear respuesta al formato API Gateway
        status_code = 201 if result['success'] else 400
        if result.get('error_code') == 'INTERNAL_ERROR':
            status_code = 500
            
        return {
            'statusCode': status_code,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(result)
        }
        
    except Exception as e:
        logger.error("Error no manejado", extra={'error': str(e)})
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'message': 'Error interno del servidor',
                'error_code': 'INTERNAL_ERROR'
            })
        }