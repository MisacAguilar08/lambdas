# Desarrollo Local de Lambdas con SAM

Este documento describe cómo configurar y ejecutar las funciones Lambda de manera local usando SAM CLI.

## Prerrequisitos

1. Instalar las siguientes herramientas:
   - [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
   - [Docker](https://www.docker.com/get-started)
   - [Python 3.9+](https://www.python.org/downloads/)
   - [AWS CLI](https://aws.amazon.com/cli/)

2. Configurar el archivo `.env` en la raíz del proyecto:
   ```
   AWS_REGION=us-east-1
   DYNAMODB_ENDPOINT=http://localhost:8000
   ```

## Estructura de Archivos

Asegúrate de tener la siguiente estructura de archivos:
```
.
├── layers/
│   ├── python/
│   │   └── utils/
│   └── requirements.txt
├── src/
│   └── functions/
├── template.yaml
├── samconfig.toml
└── .env
```

## Configuración del Entorno Local

### 1. Iniciar DynamoDB Local

En una terminal dedicada, ejecuta:
```bash
docker run -p 8000:8000 amazon/dynamodb-local
```

### 2. Crear Tablas en DynamoDB Local

En otra terminal, ejecuta:
```bash
aws dynamodb create-table \
    --table-name payments \
    --attribute-definitions AttributeName=id,AttributeType=S \
    --key-schema AttributeName=id,KeyType=HASH \
    --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
    --endpoint-url http://localhost:8000
```

Para verificar la creación de la tabla:
```bash
aws dynamodb list-tables --endpoint-url http://localhost:8000
```

## Ejecución de Funciones Lambda

### 1. Construir el Proyecto

Primero, construye las funciones y capas:
```bash
sam build --use-container
```

### 2. Iniciar API Gateway Local

Para ejecutar todas las funciones a través del API Gateway:
```bash
sam local start-api --warm-containers EAGER
```

### 3. Probar Endpoints

Ahora puedes probar los endpoints usando curl o Postman:
```bash
# Ejemplo de GET
curl http://localhost:3000/payments

# Ejemplo de POST
curl -X POST http://localhost:3000/payments \
  -H "Content-Type: application/json" \
  -d '{"amount": 100, "description": "Test payment"}'
```

## Desarrollo y Depuración

### Reconstruir Funciones Específicas

Para reconstruir una función individual:
```bash
sam build FunctionName
```

### Invocar Funciones Individuales

Para probar una función específica sin API Gateway:
```bash
sam local invoke FunctionName --event events/event.json
```

### Actualizar Dependencias
### directo al proyecto: pip install -r layers/requirements.txt -t layers/python/
Cuando necesites actualizar las dependencias:

1. Asegúrate de que tu entorno virtual esté activado:
```bash
source .venv/bin/activate  # En Linux/Mac
.venv\Scripts\activate     # En Windows
```

2. Instala las dependencias en tu entorno virtual:
```bash
pip install -r layers/requirements.txt
```

3. Prepara las layers para SAM:
```bash
python scripts/prepare_layers.py
```

4. Construye el proyecto:
```bash
sam build --use-container
```

Este método mantiene tu proyecto limpio ya que:
- Las dependencias principales se mantienen en tu entorno virtual
- Solo se copian las dependencias necesarias a `layers/python/` durante el build
- El directorio `layers/python/` puede agregarse a `.gitignore`

## Consejos de Desarrollo

1. **Cambios en el Código**:
   - Al modificar el código de una función:
     1. Detener API Gateway (Ctrl+C)
     2. Ejecutar `sam build`
     3. Reiniciar API Gateway

2. **Desarrollo Eficiente**:
   - Mantén dos terminales abiertas:
     - Terminal 1: DynamoDB Local
     - Terminal 2: SAM Local API
   - Usa una tercera terminal para rebuilds y pruebas

3. **Variables de Entorno**:
   - El entorno local usa `AWS_SAM_LOCAL=true`
   - Las funciones se conectarán automáticamente a DynamoDB local
   - Revisa `template.yaml` para ver todas las variables de entorno disponibles

4. **Logs y Depuración**:
   - Los logs aparecerán en la terminal donde ejecutas SAM
   - Usa `console.log()` o `print()` para depuración
   - Revisa los logs en tiempo real con:
     ```bash
     sam logs -n FunctionName --tail
     ```