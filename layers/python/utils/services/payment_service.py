from typing import Dict, Any, Optional, List
from utils.database.dynamodb import DynamoDBClient
from utils.logger import get_logger
from decimal import Decimal
import uuid
from datetime import datetime

class PaymentService:
    """
    Capa de servicio para la gestión de pagos.
    Implementa la lógica de negocio y actúa como intermediario entre el handler y la base de datos.
    """
    
    def __init__(self):
        """Inicializa el servicio con su cliente DynamoDB."""
        self.db_client = DynamoDBClient('payments')
        self.logger = get_logger("payment_service")

    def _validate_payment_data(self, payment_data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Valida los datos del pago.
        
        Args:
            payment_data: Datos del pago a validar
            
        Returns:
            tuple: (es_válido, mensaje_error)
        """
        required_fields = ['amount', 'currency', 'payment_method']
        
        # Validar campos requeridos
        for field in required_fields:
            if field not in payment_data:
                return False, f"Campo requerido faltante: {field}"
        
        # Validar monto
        try:
            amount = Decimal(str(payment_data['amount']))
            if amount <= 0:
                return False, "El monto debe ser mayor a 0"
        except:
            return False, "Monto inválido"
        
        # Validar moneda
        valid_currencies = ['USD', 'EUR', 'MXN']
        if payment_data['currency'] not in valid_currencies:
            return False, f"Moneda inválida. Permitidas: {', '.join(valid_currencies)}"
        
        # Validar método de pago
        valid_methods = ['credit_card', 'debit_card', 'transfer']
        if payment_data['payment_method'] not in valid_methods:
            return False, f"Método de pago inválido. Permitidos: {', '.join(valid_methods)}"
            
        return True, None

    def _enrich_payment_data(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enriquece los datos del pago con información adicional.
        
        Args:
            payment_data: Datos base del pago
            
        Returns:
            Dict: Datos del pago enriquecidos
        """
        now = datetime.utcnow().isoformat()
        
        enriched_data = {
            **payment_data,
            'payment_id': str(uuid.uuid4()),
            'status': 'pending',
            'created_at': now,
            'updated_at': now,
            'amount': Decimal(str(payment_data['amount'])),
            'metadata': {
                'source': payment_data.get('source', 'api'),
                'ip_address': payment_data.get('ip_address'),
                'user_agent': payment_data.get('user_agent')
            }
        }
        
        return enriched_data

    def register_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Registra un nuevo pago.
        
        Args:
            payment_data: Datos del pago
            
        Returns:
            Dict: Resultado de la operación
        """
        try:
            # Validar datos
            is_valid, error_message = self._validate_payment_data(payment_data)
            if not is_valid:
                self.logger.warning("Datos de pago inválidos", extra={'error': error_message})
                return {
                    'success': False,
                    'message': error_message,
                    'error_code': 'INVALID_DATA'
                }
            
            # Enriquecer datos
            enriched_payment = self._enrich_payment_data(payment_data)
            
            # Registrar en DB
            result = self.db_client.insert_item(enriched_payment)
            
            if not result['success']:
                return {
                    'success': False,
                    'message': 'Error registrando pago',
                    'error_code': 'DB_ERROR',
                    'details': result.get('error')
                }
            
            self.logger.info("Pago registrado exitosamente", extra={
                'payment_id': enriched_payment['payment_id']
            })
            
            return {
                'success': True,
                'message': 'Pago registrado exitosamente',
                'data': {
                    'payment_id': enriched_payment['payment_id'],
                    'status': enriched_payment['status'],
                    'amount': float(enriched_payment['amount']),
                    'currency': enriched_payment['currency']
                }
            }
            
        except Exception as e:
            self.logger.error("Error inesperado registrando pago", extra={'error': str(e)})
            return {
                'success': False,
                'message': 'Error interno del servidor',
                'error_code': 'INTERNAL_ERROR'
            }

    def get_payment(self, payment_id: str) -> Dict[str, Any]:
        """
        Obtiene los detalles de un pago.
        
        Args:
            payment_id: ID del pago
            
        Returns:
            Dict: Detalles del pago
        """
        try:
            result = self.db_client.get_item({'payment_id': payment_id})
            
            if not result['success']:
                return {
                    'success': False,
                    'message': 'Pago no encontrado',
                    'error_code': 'NOT_FOUND'
                }
            
            return {
                'success': True,
                'message': 'Pago encontrado',
                'data': result['data']
            }
            
        except Exception as e:
            self.logger.error("Error obteniendo pago", extra={
                'payment_id': payment_id,
                'error': str(e)
            })
            return {
                'success': False,
                'message': 'Error interno del servidor',
                'error_code': 'INTERNAL_ERROR'
            }

    def update_payment_status(
        self,
        payment_id: str,
        new_status: str,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Actualiza el estado de un pago.
        
        Args:
            payment_id: ID del pago
            new_status: Nuevo estado
            metadata: Información adicional opcional
            
        Returns:
            Dict: Resultado de la operación
        """
        try:
            # Validar estado
            valid_statuses = ['pending', 'processing', 'completed', 'failed', 'refunded']
            if new_status not in valid_statuses:
                return {
                    'success': False,
                    'message': f"Estado inválido. Permitidos: {', '.join(valid_statuses)}",
                    'error_code': 'INVALID_STATUS'
                }
            
            # Preparar actualización
            update_data = {
                'status': new_status,
                'updated_at': datetime.utcnow().isoformat()
            }
            
            if metadata:
                update_data['metadata'] = metadata
            
            # Actualizar en DB
            result = self.db_client.update_item(
                key={'payment_id': payment_id},
                update_attrs=update_data
            )
            
            if not result['success']:
                return {
                    'success': False,
                    'message': 'Error actualizando pago',
                    'error_code': 'DB_ERROR',
                    'details': result.get('error')
                }
            
            self.logger.info("Estado de pago actualizado", extra={
                'payment_id': payment_id,
                'new_status': new_status
            })
            
            return {
                'success': True,
                'message': 'Estado de pago actualizado',
                'data': result['data']
            }
            
        except Exception as e:
            self.logger.error("Error actualizando estado de pago", extra={
                'payment_id': payment_id,
                'error': str(e)
            })
            return {
                'success': False,
                'message': 'Error interno del servidor',
                'error_code': 'INTERNAL_ERROR'
            }

    def list_payments(
        self,
        status: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Lista pagos con filtros opcionales.
        
        Args:
            status: Filtrar por estado
            start_date: Fecha inicial
            end_date: Fecha final
            
        Returns:
            Dict: Lista de pagos
        """
        try:
            # Construir expresiones de consulta
            key_condition = "created_at BETWEEN :start AND :end"
            expression_values = {
                ':start': start_date or '2000-01-01',
                ':end': end_date or datetime.utcnow().isoformat()
            }
            
            # Agregar filtro por estado si se especifica
            filter_expression = None
            if status:
                filter_expression = "status = :status"
                expression_values[':status'] = status
            
            # Consultar DB
            result = self.db_client.query_items(
                key_condition=key_condition,
                expression_values=expression_values,
                filter_expression=filter_expression,
                index_name='created_at-index'
            )
            
            if not result['success']:
                return {
                    'success': False,
                    'message': 'Error listando pagos',
                    'error_code': 'DB_ERROR',
                    'details': result.get('error')
                }
            
            return {
                'success': True,
                'message': 'Pagos obtenidos exitosamente',
                'data': result['data'],
                'count': result['count']
            }
            
        except Exception as e:
            self.logger.error("Error listando pagos", extra={'error': str(e)})
            return {
                'success': False,
                'message': 'Error interno del servidor',
                'error_code': 'INTERNAL_ERROR'
            }