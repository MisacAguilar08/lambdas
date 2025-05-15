# Guía de Despliegue SAM

Esta guía proporciona instrucciones detalladas para construir, desplegar y gestionar tu aplicación SAM en AWS.

## Prerrequisitos

1. AWS CLI instalado y configurado
```bash
aws configure
```

2. SAM CLI instalado
```bash
# Para Mac
brew tap aws/tap
brew install aws-sam-cli

# Para Windows
# Descargar el instalador de: https://github.com/aws/aws-sam-cli/releases/latest/download/AWS_SAM_CLI_64_PY3.msi
```

3. Docker instalado y corriendo (necesario para construir las capas Lambda)

## Construcción

1. Construir la aplicación:
```bash
sam build
```

2. Para construir en una plataforma específica:
```bash
sam build --use-container
```

## Primer Despliegue

1. Desplegar por primera vez (modo interactivo):
```bash
sam deploy --guided
```

Durante el despliegue guiado, se te pedirá:
- Stack Name (nombre-de-tu-stack)
- AWS Region (región de AWS)
- Confirmar los cambios IAM
- Permitir crear roles IAM
- Guardar argumentos para futuros despliegues

2. El comando creará un archivo `samconfig.toml` con tu configuración

## Actualizaciones y Redeployments

1. Después de hacer cambios en el código:
```bash
sam build
sam deploy
```

2. Para forzar un reemplazo de la función:
```bash
sam deploy --force-upload
```

## Invocar la Función Lambda

1. Usando AWS CLI:
```bash
# Usando el archivo de evento completo
aws lambda invoke \
    --function-name nombre-stack-register-payment \
    --cli-binary-format raw-in-base64-out \
    --payload file://events/event.json \
    response.json

# Usando el archivo de pago simplificado
aws lambda invoke \
    --function-name nombre-stack-register-payment \
    --cli-binary-format raw-in-base64-out \
    --payload file://events/payment.json \
    response.json
```

2. Usando SAM Local:
```bash
sam local invoke RegisterPayment --event events/event.json
```

## Pruebas con cURL

Después del despliegue, SAM te proporcionará una URL de API Gateway. Usa esa URL para las pruebas:

```bash
# Reemplaza {api-url} con tu URL de API Gateway
curl -X POST \
  https://{api-url}/Prod/payments \
  -H 'Content-Type: application/json' \
  -d '{
    "payment_id": "PAY123",
    "amount": 100.50,
    "currency": "USD",
    "description": "Test payment",
    "customer_id": "CUST456",
    "payment_method": "credit_card",
    "status": "pending"
  }'
```

## Monitoreo y Logs

1. Ver logs en tiempo real:
```bash
sam logs -n RegisterPayment --stack-name nombre-stack --tail
```

2. Ver logs de un período específico:
```bash
sam logs -n RegisterPayment --stack-name nombre-stack --start-time '5mins ago'
```

3. Filtrar logs por patrón:
```bash
sam logs -n RegisterPayment --stack-name nombre-stack --filter "ERROR"
```

## Gestión de Recursos

1. Listar recursos del stack:
```bash
aws cloudformation describe-stack-resources --stack-name nombre-stack
```

2. Ver detalles de la función Lambda:
```bash
aws lambda get-function --function-name nombre-stack-register-payment
```

3. Ver métricas en CloudWatch:
```bash
aws cloudwatch get-metric-statistics \
    --namespace AWS/Lambda \
    --metric-name Invocations \
    --dimensions Name=FunctionName,Value=nombre-stack-register-payment \
    --start-time $(date -u -v-1H +"%Y-%m-%dT%H:%M:%SZ") \
    --end-time $(date -u +"%Y-%m-%dT%H:%M:%SZ") \
    --period 3600 \
    --statistics Sum
```

## Eliminar la Aplicación

Si necesitas eliminar todos los recursos:
```bash
sam delete
```

## Solución de Problemas Comunes

1. Error "No updates to be performed":
   - Asegúrate de haber hecho `sam build` antes de `sam deploy`
   - Intenta con `sam deploy --force-upload`

2. Error de permisos IAM:
   - Verifica que tu usuario AWS tenga los permisos necesarios
   - Usa `--capabilities CAPABILITY_IAM` en el deploy

3. Error de conexión a DynamoDB:
   - Verifica que la tabla existe
   - Confirma los permisos IAM de la función Lambda

4. Logs no aparecen:
   - Espera unos segundos después de la invocación
   - Verifica que el rol de ejecución tenga permisos CloudWatch

## Comandos Útiles Adicionales

1. Validar template:
```bash
sam validate
```

2. Generar evento de ejemplo:
```bash
sam local generate-event apigateway http-api-proxy > event.json
```

3. Listar endpoints API:
```bash
aws apigateway get-rest-apis
```

4. Ver configuración de la función:
```bash
aws lambda get-function-configuration --function-name nombre-stack-register-payment
```

## Notas Importantes

- Siempre haz `sam build` después de cambios en el código
- Mantén seguros tus secretos usando AWS Secrets Manager o SSM Parameter Store
- Revisa los logs regularmente para monitorear el comportamiento de la aplicación
- Considera usar diferentes stacks para desarrollo y producción
- Haz backups regulares de tus datos en DynamoDB