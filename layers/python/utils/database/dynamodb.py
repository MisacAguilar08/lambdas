import boto3
from typing import Dict, Any, List, Optional
from botocore.exceptions import ClientError
from utils.logger import get_logger
from decimal import Decimal
import json

dynamodb = boto3.resource('dynamodb')

class DynamoDBClient:
    """Cliente para operaciones en DynamoDB con manejo de errores y logging."""
    
    def __init__(self, table_name: str):
        """
        Inicializa el cliente DynamoDB.
        
        Args:
            table_name (str): Nombre de la tabla DynamoDB
        """
        self.table = dynamodb.Table(table_name)
        self.logger = get_logger("dynamodb_client").append_keys(table=table_name)

    def _handle_decimal(self, obj: Any) -> Any:
        """
        Convierte Decimal a float para serialización JSON.
        
        Args:
            obj: Objeto a convertir
            
        Returns:
            Objeto convertido
        """
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, dict):
            return {k: self._handle_decimal(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._handle_decimal(x) for x in obj]
        return obj

    def insert_item(self, item: Dict[str, Any], condition: Optional[str] = None) -> Dict[str, Any]:
        """
        Inserta un nuevo item en la tabla.
        
        Args:
            item (Dict): Item a insertar
            condition (str, optional): Expresión de condición para la inserción
            
        Returns:
            Dict: Respuesta de DynamoDB
            
        Raises:
            ClientError: Si ocurre un error en la operación
        """
        try:
            self.logger.info("Iniciando la operación de inserción en la base de datos")
            params = {
                'Item': item
            }

            self.logger.info("Preparando los parámetros para la inserción:",params)
            
            if condition:
                params['ConditionExpression'] = condition
                
            response = self.table.put_item(**params)
            self.logger.info("Operación de inserción completada exitosamente", response)
            self.logger.info("Item insertado exitosamente", extra={
                'item_id': item.get('id'),
                'operation': 'insert'
            })
            
            return {
                'success': True,
                'message': 'Item insertado correctamente',
                'data': self._handle_decimal(item)
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            self.logger.error("Error insertando item", extra={
                'error_code': error_code,
                'error_message': error_message,
                'item_id': item.get('id')
            })
            
            if error_code == 'ConditionalCheckFailedException':
                return {
                    'success': False,
                    'message': 'El item ya existe',
                    'error': error_message
                }
            
            return {
                'success': False,
                'message': 'Error insertando item',
                'error': error_message
            }

    def update_item(
        self,
        key: Dict[str, Any],
        update_attrs: Dict[str, Any],
        condition: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Actualiza un item existente.
        
        Args:
            key (Dict): Clave primaria del item
            update_attrs (Dict): Atributos a actualizar
            condition (str, optional): Expresión de condición
            
        Returns:
            Dict: Respuesta de DynamoDB
        """
        try:
            # Construir expresión de actualización
            update_expression = "SET "
            expression_values = {}
            expression_names = {}
            
            for i, (key, value) in enumerate(update_attrs.items()):
                placeholder = f":val{i}"
                attr_name = f"#attr{i}"
                update_expression += f"{attr_name} = {placeholder}, "
                expression_values[placeholder] = value
                expression_names[attr_name] = key
            
            # Remover última coma
            update_expression = update_expression.rstrip(", ")
            
            params = {
                'Key': key,
                'UpdateExpression': update_expression,
                'ExpressionAttributeValues': expression_values,
                'ExpressionAttributeNames': expression_names,
                'ReturnValues': 'ALL_NEW'
            }
            
            if condition:
                params['ConditionExpression'] = condition
            
            response = self.table.update_item(**params)
            updated_item = response.get('Attributes', {})
            
            self.logger.info("Item actualizado exitosamente", extra={
                'item_id': key.get('id'),
                'operation': 'update'
            })
            
            return {
                'success': True,
                'message': 'Item actualizado correctamente',
                'data': self._handle_decimal(updated_item)
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            self.logger.error("Error actualizando item", extra={
                'error_code': error_code,
                'error_message': error_message,
                'item_id': key.get('id')
            })
            
            if error_code == 'ConditionalCheckFailedException':
                return {
                    'success': False,
                    'message': 'El item no existe o no cumple la condición',
                    'error': error_message
                }
            
            return {
                'success': False,
                'message': 'Error actualizando item',
                'error': error_message
            }

    def delete_item(
        self,
        key: Dict[str, Any],
        condition: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Elimina un item de la tabla.
        
        Args:
            key (Dict): Clave primaria del item
            condition (str, optional): Expresión de condición
            
        Returns:
            Dict: Respuesta de DynamoDB
        """
        try:
            params = {
                'Key': key,
                'ReturnValues': 'ALL_OLD'
            }
            
            if condition:
                params['ConditionExpression'] = condition
            
            response = self.table.delete_item(**params)
            deleted_item = response.get('Attributes', {})
            
            self.logger.info("Item eliminado exitosamente", extra={
                'item_id': key.get('id'),
                'operation': 'delete'
            })
            
            return {
                'success': True,
                'message': 'Item eliminado correctamente',
                'data': self._handle_decimal(deleted_item)
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            self.logger.error("Error eliminando item", extra={
                'error_code': error_code,
                'error_message': error_message,
                'item_id': key.get('id')
            })
            
            if error_code == 'ConditionalCheckFailedException':
                return {
                    'success': False,
                    'message': 'El item no existe o no cumple la condición',
                    'error': error_message
                }
            
            return {
                'success': False,
                'message': 'Error eliminando item',
                'error': error_message
            }

    def get_item(self, key: Dict[str, Any]) -> Dict[str, Any]:
        """
        Obtiene un item por su clave primaria.
        
        Args:
            key (Dict): Clave primaria del item
            
        Returns:
            Dict: Item encontrado o error
        """
        try:
            response = self.table.get_item(Key=key)
            item = response.get('Item', {})
            
            if not item:
                return {
                    'success': False,
                    'message': 'Item no encontrado',
                    'data': None
                }
            
            self.logger.info("Item obtenido exitosamente", extra={
                'item_id': key.get('id'),
                'operation': 'get'
            })
            
            return {
                'success': True,
                'message': 'Item obtenido correctamente',
                'data': self._handle_decimal(item)
            }
            
        except ClientError as e:
            error_message = e.response['Error']['Message']
            
            self.logger.error("Error obteniendo item", extra={
                'error_code': e.response['Error']['Code'],
                'error_message': error_message,
                'item_id': key.get('id')
            })
            
            return {
                'success': False,
                'message': 'Error obteniendo item',
                'error': error_message
            }

    def query_items(
        self,
        key_condition: str,
        expression_values: Dict[str, Any],
        index_name: Optional[str] = None,
        filter_expression: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Realiza una consulta en la tabla.
        
        Args:
            key_condition (str): Expresión de condición de clave
            expression_values (Dict): Valores para la expresión
            index_name (str, optional): Nombre del índice secundario
            filter_expression (str, optional): Expresión de filtro adicional
            
        Returns:
            Dict: Items encontrados o error
        """
        try:
            params = {
                'KeyConditionExpression': key_condition,
                'ExpressionAttributeValues': expression_values
            }
            
            if index_name:
                params['IndexName'] = index_name
                
            if filter_expression:
                params['FilterExpression'] = filter_expression
            
            response = self.table.query(**params)
            items = response.get('Items', [])
            
            self.logger.info("Query ejecutado exitosamente", extra={
                'count': len(items),
                'operation': 'query'
            })
            
            return {
                'success': True,
                'message': 'Query ejecutado correctamente',
                'data': self._handle_decimal(items),
                'count': len(items)
            }
            
        except ClientError as e:
            error_message = e.response['Error']['Message']
            
            self.logger.error("Error ejecutando query", extra={
                'error_code': e.response['Error']['Code'],
                'error_message': error_message
            })
            
            return {
                'success': False,
                'message': 'Error ejecutando query',
                'error': error_message
            }

    def batch_write(self, items: List[Dict[str, Any]], operation: str = 'insert') -> Dict[str, Any]:
        """
        Realiza operaciones batch (insert/delete) en la tabla.
        
        Args:
            items (List[Dict]): Lista de items
            operation (str): 'insert' o 'delete'
            
        Returns:
            Dict: Resultado de la operación
        """
        try:
            with self.table.batch_writer() as batch:
                for item in items:
                    if operation == 'insert':
                        batch.put_item(Item=item)
                    elif operation == 'delete':
                        batch.delete_item(Key=item)
            
            self.logger.info("Batch operation completada", extra={
                'operation': f'batch_{operation}',
                'items_count': len(items)
            })
            
            return {
                'success': True,
                'message': f'Batch {operation} completado correctamente',
                'count': len(items)
            }
            
        except ClientError as e:
            error_message = e.response['Error']['Message']
            
            self.logger.error("Error en batch operation", extra={
                'error_code': e.response['Error']['Code'],
                'error_message': error_message,
                'operation': f'batch_{operation}'
            })
            
            return {
                'success': False,
                'message': f'Error en batch {operation}',
                'error': error_message
            }

# Ejemplo de uso:
"""
# Inicializar cliente
db = DynamoDBClient('mi-tabla')

# Insertar item
item = {
    'id': '123',
    'nombre': 'Ejemplo',
    'precio': Decimal('99.99')
}
result = db.insert_item(item)

# Actualizar item
key = {'id': '123'}
updates = {'nombre': 'Nuevo Nombre', 'precio': Decimal('149.99')}
result = db.update_item(key, updates)

# Eliminar item
result = db.delete_item(key)

# Consultar items
query_result = db.query_items(
    key_condition='id = :id',
    expression_values={':id': '123'}
)

# Operación batch
items = [
    {'id': '1', 'nombre': 'Item 1'},
    {'id': '2', 'nombre': 'Item 2'}
]
result = db.batch_write(items, 'insert')
"""