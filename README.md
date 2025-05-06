# AWS Lambda Project with SAM

Este proyecto demuestra cómo configurar múltiples funciones Lambda usando AWS SAM (Serverless Application Model) con una capa compartida de dependencias (Lambda Layer) y autenticación mediante Custom Authorizer.

## Estructura del Proyecto

```
.
├── .github/
│   └── workflows/
│       └── deploy-lambda.yml    # Configuración de GitHub Actions
├── layers/
│   ├── python/                  # Directorio donde se instalan las dependencias de la layer
│   └── requirements.txt         # Dependencias compartidas para todas las funciones
├── src/
│   ├── hello_world/            # Primera función Lambda
│   │   ├── app.py              # Código de la función
│   │   └── requirements.txt     # Dependencias específicas (si las hay)
│   ├── process_data/           # Segunda función Lambda
│   │   ├── app.py              # Código de la función
│   │   └── requirements.txt     # Dependencias específicas (si las hay)
│   └── authorizer/             # Custom Authorizer Lambda
│       ├── app.py              # Código del authorizer
│       └── requirements.txt     # Dependencias específicas
├── template.yaml               # Plantilla SAM
└── Makefile                   # Comandos útiles para el desarrollo
```

## Componentes Principales

### 1. Lambda Layer

La Layer se define en `template.yaml`:
```yaml
CommonDependenciesLayer:
  Type: AWS::Serverless::LayerVersion
  Properties:
    LayerName: common-dependencies
    Description: Common dependencies for Lambda functions
    ContentUri: layers/
    CompatibleRuntimes:
      - python3.11
    RetentionPolicy: Retain
```

Las dependencias compartidas se especifican en `layers/requirements.txt`:
- pandas
- numpy
- pytz
- PyJWT
- pytest

### 2. Funciones Lambda

Cada función Lambda está configurada en `template.yaml` y usa la layer compartida:
```yaml
HelloWorldFunction:
  Type: AWS::Serverless::Function
  Properties:
    FunctionName: !Sub ${AWS::StackName}-hello-world
    CodeUri: src/hello_world/
    Handler: app.lambda_handler
    Runtime: python3.11
    Layers:
      - !Ref CommonDependenciesLayer
```

### 3. Sistema de Autenticación y Autorización

El proyecto implementa un sistema de autenticación basado en JWT (JSON Web Tokens) con un Custom Authorizer para proteger los endpoints de la API.

#### Tokens de Autenticación

##### Access Token
Token JWT de corta duración para autenticar solicitudes a la API.

**Características:**
- **Duración:** 1 hora
- **Propósito:** Autenticación de solicitudes a la API
- **Formato:** JWT (JSON Web Token)
- **Algoritmo:** HS256
- **Claims:**
  ```json
  {
    "sub": "user123",           // ID del usuario
    "iat": 1234567890,         // Timestamp de emisión
    "exp": 1234571490,         // Timestamp de expiración
    "iss": "lambda-api",       // Emisor del token
    "type": "access"           // Tipo de token
  }
  ```

##### Refresh Token
Token JWT de larga duración para renovar access tokens expirados.

**Características:**
- **Duración:** 7 días
- **Propósito:** Renovar access tokens expirados
- **Formato:** JWT (JSON Web Token)
- **Algoritmo:** HS256
- **Claims:**
  ```json
  {
    "sub": "user123",           // ID del usuario
    "iat": 1234567890,         // Timestamp de emisión
    "exp": 1235172690,         // Timestamp de expiración (7 días)
    "iss": "lambda-api",       // Emisor del token
    "type": "refresh"          // Tipo de token
  }
  ```

#### Custom Authorizer
Función Lambda que valida los tokens en las solicitudes API:

```yaml
Auth:
  DefaultAuthorizer: CustomAuthorizer
  Authorizers:
    CustomAuthorizer:
      FunctionArn: !GetAtt CustomAuthorizerFunction.Arn
      FunctionPayloadType: TOKEN
      Identity:
        Header: Authorization
        ValidationExpression: "^Bearer [-0-9a-zA-Z\._]*$"
        ReauthorizeEvery: 300
```

**Características:**
- Validación de tokens JWT
- Reautorización cada 5 minutos
- Validación estricta del formato del token
- Integración con secretos para la firma JWT

#### Endpoints de Autenticación

##### 1. Generar Tokens
**Endpoint:** `/token`
**Método:** POST

**Request:**
```json
{
    "grant_type": "password",
    "user_id": "user123"
}
```

**Response:**
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "expires_in": 3600,
    "token_type": "Bearer"
}
```

##### 2. Renovar Access Token
**Endpoint:** `/token`
**Método:** POST

**Request:**
```json
{
    "grant_type": "refresh_token",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response:**
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "expires_in": 3600,
    "token_type": "Bearer"
}
```

#### Manejo de Errores

1. **401 Unauthorized:**
   ```json
   {
       "error": "Refresh token expirado"
   }
   ```
   ```json
   {
       "error": "Refresh token inválido"
   }
   ```

2. **400 Bad Request:**
   ```json
   {
       "error": "grant_type inválido"
   }
   ```
   ```json
   {
       "error": "user_id es requerido"
   }
   ```

#### Buenas Prácticas de Seguridad

1. **Almacenamiento:**
   - Access Token: Almacenar en memoria (no en localStorage)
   - Refresh Token: Almacenar en HttpOnly cookies

2. **Renovación:**
   - Implementar renovación automática del access token
   - Renovar antes de la expiración para evitar interrupciones
   - Manejar errores de renovación redirigiendo al login

3. **Seguridad:**
   - Usar siempre HTTPS
   - No incluir información sensible en los tokens
   - Implementar revocación de tokens cuando sea necesario

### 4. GitHub Actions Workflow

El workflow (`.github/workflows/deploy-lambda.yml`) automatiza el despliegue y se ejecuta en las siguientes situaciones:

1. **Push a main** (solo archivos relevantes):
   - Cambios en `/src/**`
   - Cambios en `/layers/**`
   - Cambios en `template.yaml`

2. **Pull Requests a main**:
   - Verifica el build y despliegue
   - Solo para cambios en código y configuración

3. **Creación de Release**:
   - Se ejecuta automáticamente al crear un nuevo release
   - Ideal para despliegues a producción

4. **Manual (workflow_dispatch)**:
   - Puede ser ejecutado manualmente desde GitHub
   - Permite seleccionar el ambiente (dev/staging/prod)
   - Opción para habilitar logs de debug

El workflow realiza las siguientes acciones:
1. Configura el entorno Python
2. Instala dependencias del sistema
3. Instala AWS SAM CLI
4. Construye la Lambda Layer
5. Configura credenciales AWS
6. Construye y despliega la aplicación

Para ejecutar manualmente:
1. Ir a la pestaña "Actions" en GitHub
2. Seleccionar "Deploy Lambda"
3. Click en "Run workflow"
4. Seleccionar la rama y configurar opciones
5. Click en "Run workflow"

### 4. Makefile

El Makefile proporciona comandos útiles:

- `make build`: Construye el proyecto usando SAM
- `make clean`: Limpia archivos generados
- `make deploy`: Despliega la aplicación
- `make build-layer`: Construye la Lambda Layer
- `make install-deps`: Instala dependencias localmente

## Pasos de Implementación

1. **Configuración Inicial**
   - Crear estructura de directorios
   - Configurar template.yaml básico
   - Crear Makefile inicial

2. **Configuración de Layer**
   - Crear directorio layers
   - Definir dependencias compartidas
   - Configurar Layer en template.yaml

3. **Configuración de Funciones**
   - Crear directorios para cada función
   - Implementar código de las funciones
   - Asociar funciones con la Layer

4. **Configuración de CI/CD**
   - Crear workflow de GitHub Actions
   - Configurar pasos de build y deploy
   - Manejar credenciales AWS

## Uso

1. **Configuración Local**
   ```bash
   # Instalar dependencias
   make install-deps

   # Construir Layer
   make build-layer

   # Construir proyecto
   make build
   ```

2. **Despliegue**
   ```bash
   # Desplegar a AWS
   make deploy
   ```

3. **Desarrollo**
   - Añadir nuevas dependencias a `layers/requirements.txt`
   - Implementar código en los directorios de las funciones
   - Commit y push para despliegue automático

## Requisitos

- Python 3.11
- AWS CLI configurado
- AWS SAM CLI
- Credenciales AWS con permisos adecuados

## Secretos Necesarios en GitHub

Para el despliegue automático, configurar en GitHub:
- `AWS_ACCESS_KEY_ID`: ID de clave de acceso de AWS
- `AWS_SECRET_ACCESS_KEY`: Clave secreta de acceso de AWS
- `AWS_REGION`: Región de AWS donde se desplegará
- `AUTH_TOKEN_SECRET`: Secreto para firmar y validar tokens JWT



## Monitoreo y Solución de Problemas

### CloudWatch Logs

Cada función genera logs en formato JSON con la siguiente información:
- Timestamp
- Nivel de log (INFO, ERROR, etc.)
- Nombre del servicio
- Detalles de la solicitud/respuesta
- Trazas de error (si aplica)

Para ver los logs:
1. Ir a CloudWatch en la consola AWS
2. Navegar a Log Groups
3. Buscar el grupo correspondiente a la función:
   - `/aws/lambda/lambdas-init-hello-world`
   - `/aws/lambda/lambdas-init-process-data`
   - `/aws/lambda/lambdas-init-custom-authorizer`
   - `/aws/lambda/lambdas-init-token-generator`

### X-Ray Tracing

El proyecto tiene habilitado X-Ray para todas las funciones:
- Visualización de latencias
- Identificación de cuellos de botella
- Análisis de dependencias entre servicios
- Mapeo de errores en la cadena de llamadas

### Problemas Comunes

1. **Error: Token inválido**
   - Verificar que el token no haya expirado
   - Asegurar que AUTH_TOKEN_SECRET sea el mismo usado para generar el token
   - Validar el formato del header Authorization

2. **Error: Unable to upload artifact**
   - Verificar que existe el directorio layers/python
   - Asegurar que requirements.txt está presente
   - Confirmar que las dependencias se instalaron correctamente

3. **Error: Deployment failed**
   - Revisar los logs de CloudFormation
   - Verificar permisos de IAM
   - Comprobar límites de servicio AWS

### Métricas Importantes

CloudWatch recopila automáticamente:
- Invocaciones por función
- Errores y timeouts
- Duración de ejecución
- Memoria utilizada
- Concurrencia

## Mejores Prácticas

### Desarrollo
- Usar entornos virtuales para desarrollo local
- Mantener requirements.txt actualizado
- Seguir principios de IaC (Infrastructure as Code)
- Implementar pruebas unitarias

### Seguridad
- Rotar regularmente AUTH_TOKEN_SECRET
- Mantener las dependencias actualizadas
- Usar el principio de mínimo privilegio en IAM
- Implementar rate limiting en API Gateway

### Operaciones
- Monitorear costos regularmente
- Configurar alarmas para errores y latencia
- Mantener documentación actualizada
- Realizar backups de configuración

## Endpoints API

1. Token Generator Function
   - Path: `/token`
   - Método: POST
   - Autenticación: No requiere
   - Cuerpo de la solicitud:
     ```json
     {
         "user_id": "tu-id-de-usuario"
     }
     ```
   - Respuesta:
     ```json
     {
         "token": "eyJhbGciOiJIUzI1NiIs...",
         "expires_in": 86400,
         "token_type": "Bearer"
     }
     ```

2. Hello World Function
   - Path: `/hello`
   - Método: GET
   - Autenticación: Requiere token JWT válido
   - Retorna: Mensaje de saludo y timestamp
   - Ejemplo de uso:
     ```bash
     curl https://tu-api.execute-api.region.amazonaws.com/Prod/hello \
       -H "Authorization: Bearer tu-token-aquí"
     ```

3. Process Data Function
   - Path: `/process`
   - Método: POST
   - Autenticación: Requiere token JWT válido
   - Retorna: Estadísticas de datos procesados
   - Ejemplo de uso:
     ```bash
     curl -X POST https://tu-api.execute-api.region.amazonaws.com/Prod/process \
       -H "Authorization: Bearer tu-token-aquí" \
       -H "Content-Type: application/json" \
       -d '{"data": "ejemplo"}'
     ```

### Autenticación de Endpoints

Todos los endpoints (excepto `/token`) requieren autenticación mediante token JWT:

1. **Obtención del Token**:
   ```bash
   curl -X POST https://tu-api.execute-api.region.amazonaws.com/Prod/token \
     -H "Content-Type: application/json" \
     -d '{"user_id": "123"}'
   ```

2. **Header Requerido**:
   ```
   Authorization: Bearer <token>
   ```

3. **Formato del Token**:
   - Debe ser un JWT válido
   - Firmado con el secreto configurado en AUTH_TOKEN_SECRET
   - Debe incluir claims estándar:
     - `sub`: ID del usuario
     - `exp`: Tiempo de expiración (24 horas desde la emisión)
     - `iat`: Tiempo de emisión
     - `iss`: Emisor del token (lambda-api)

4. **Manejo de Errores**:
   - Token expirado: HTTP 401
   - Token inválido: HTTP 401
   - Token mal formado: HTTP 400
   - Token faltante: HTTP 401

5. **Seguridad**:
   - Los tokens expiran después de 24 horas
   - El authorizer revalida los tokens cada 5 minutos
   - Se utiliza HTTPS para todas las comunicaciones
   - Los tokens son firmados con HS256

3. **Ejemplo de Uso**:
   ```bash
   # Petición GET
   curl -X GET https://your-api.execute-api.region.amazonaws.com/Prod/hello \
     -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
     -H "Content-Type: application/json"

   # Petición POST
   curl -X POST https://your-api.execute-api.region.amazonaws.com/Prod/process \
     -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
     -H "Content-Type: application/json" \
     -d '{"data": "example"}'
   ```

### Headers CORS Permitidos

Los endpoints permiten los siguientes headers CORS:
- Content-Type
- X-Amz-Date
- Authorization
- X-Api-Key
- X-Amz-Security-Token

### Ejemplo de Uso

```bash
# Ejemplo de petición con token
curl -X GET https://your-api.execute-api.region.amazonaws.com/Prod/hello \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."

# Ejemplo de petición POST
curl -X POST https://your-api.execute-api.region.amazonaws.com/Prod/process \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -H "Content-Type: application/json" \
  -d '{"data": "example"}'
```

## Mantenimiento

1. **Actualizar Dependencias**
   - Modificar `layers/requirements.txt`
   - Ejecutar `make build-layer`
   - Desplegar cambios

2. **Añadir Nueva Función**
   - Crear nuevo directorio en `src/`
   - Añadir configuración en `template.yaml`
   - Actualizar documentación

3. **Depuración**
   - Revisar logs en CloudWatch
   - Usar `sam local` para pruebas locales
   - Verificar configuración de Layer

## Guía Detallada para Configuración de Lambda Layers

### 1. Estructura de Archivos para Layer
```
layers/
├── python/          # Directorio donde se instalarán las dependencias
└── requirements.txt # Lista de dependencias compartidas
```

### 2. Modificaciones en template.yaml

```yaml
# 1. Definir el recurso Layer
Resources:
  CommonDependenciesLayer:
    Type: AWS::Serverless::LayerVersion
    Properties:
      LayerName: common-dependencies
      Description: Common dependencies for Lambda functions
      ContentUri: layers/
      CompatibleRuntimes:
        - python3.11
      RetentionPolicy: Retain

  # 2. Añadir la Layer a las funciones Lambda
  MyFunction:
    Type: AWS::Serverless::Function
    Properties:
      # ... otras propiedades ...
      Layers:
        - !Ref CommonDependenciesLayer

# 3. Opcional: Añadir Outputs para la Layer
Outputs:
  CommonDependenciesLayerArn:
    Description: ARN of the common dependencies layer
    Value: !Ref CommonDependenciesLayer
  CommonDependenciesLayerVersion:
    Description: Version of the common dependencies layer
    Value: !Ref CommonDependenciesLayer
```

### 3. Modificaciones en deploy-lambda.yml

```yaml
jobs:
  deploy:
    steps:
      # ... pasos anteriores ...

      # 1. Añadir paso para construir la Layer
      - name: Build Lambda Layer
        run: |
          make build-layer

      # 2. Asegurarse que este paso esté después de construir la Layer
      - name: SAM Build
        run: sam build --use-container

      # 3. Asegurarse que el deploy incluya los permisos necesarios
      - name: SAM Deploy
        run: |
          sam deploy --stack-name lambdas-init \
            --no-confirm-changeset \
            --no-fail-on-empty-changeset \
            --capabilities CAPABILITY_IAM
```

### 4. Modificaciones en Makefile

```makefile
# 1. Añadir comando para construir la Layer
build-layer:
	mkdir -p layers/python
	python -m pip install -r layers/requirements.txt -t layers/python/

# 2. Modificar el clean para incluir la Layer
clean:
	rm -rf .aws-sam/
	rm -rf layers/python/*

# 3. Asegurarse que build use contenedores
build:
	sam build --use-container
```

### 5. Pasos de Implementación

1. **Crear estructura de Layer**:
   ```bash
   mkdir -p layers/python
   ```

2. **Crear requirements.txt para Layer**:
   ```bash
   # layers/requirements.txt
   pandas==1.5.3
   numpy==1.24.3
   pytz==2023.3
   ```

3. **Limpiar requirements.txt de las funciones individuales**:
   - Mover dependencias compartidas al requirements.txt de la Layer
   - Dejar solo dependencias específicas en cada función

4. **Construir Layer localmente**:
   ```bash
   make build-layer
   ```

5. **Verificar estructura**:
   ```
   layers/
   ├── python/
   │   ├── numpy/
   │   ├── pandas/
   │   └── pytz/
   └── requirements.txt
   ```

### 6. Consideraciones Importantes

1. **Tamaño de Layer**:
   - Límite de 250 MB descomprimido
   - Monitorear tamaño de dependencias

2. **Versionamiento**:
   - Las Layers son versionadas automáticamente
   - Cada despliegue crea una nueva versión
   - Mantener el RetentionPolicy en Retain

3. **Permisos**:
   - Asegurar que el rol IAM tenga permisos para:
     - Crear y actualizar Layers
     - Asociar Layers a funciones
     - Eliminar versiones antiguas

4. **Optimización**:
   - Incluir solo dependencias necesarias
   - Considerar separar en múltiples Layers si es necesario
   - Limpiar versiones antiguas periódicamente

5. **Debugging**:
   - Verificar la estructura de directorios de la Layer
   - Comprobar que las dependencias se instalan correctamente
   - Revisar logs de CloudWatch para errores de importación

## Uso del Makefile

El Makefile se utiliza en dos contextos principales:

### 1. En GitHub Actions (Automatizado)

El workflow de CI/CD llama al Makefile automáticamente:
```yaml
# .github/workflows/deploy-lambda.yml
- name: Build Lambda Layer
  run: |
    make build-layer
```

Este proceso ocurre:
- Cuando se hace push a la rama main
- Cuando se activa manualmente el workflow (workflow_dispatch)

### 2. Desarrollo Local (Manual)

Los desarrolladores usan el Makefile para tareas comunes:

```bash
# Instalar dependencias de las funciones
make install-deps

# Construir la Layer con las dependencias compartidas
make build-layer

# Construir el proyecto completo
make build

# Desplegar a AWS
make deploy

# Limpiar archivos generados
make clean
```

### Cuándo Usar Cada Comando

1. **make install-deps**:
   - Al iniciar el proyecto por primera vez
   - Cuando se añaden nuevas dependencias específicas a una función
   - Después de clonar el repositorio

2. **make build-layer**:
   - Cuando se modifican las dependencias compartidas en layers/requirements.txt
   - Antes de hacer un despliegue local
   - Para probar la instalación de dependencias

3. **make build**:
   - Antes de hacer un despliegue local
   - Para verificar que todo compila correctamente
   - Cuando se modifican las funciones Lambda

4. **make deploy**:
   - Para desplegar manualmente a AWS
   - Cuando se necesita probar en el ambiente de AWS
   - Después de hacer cambios locales

5. **make clean**:
   - Cuando se quiere limpiar archivos generados
   - Si hay problemas de caché
   - Antes de un rebuild completo

### Flujo de Trabajo Típico

1. **Desarrollo Inicial**:
   ```bash
   make install-deps
   make build-layer
   make build
   make deploy
   ```

2. **Cambios en Dependencias Compartidas**:
   ```bash
   make clean
   make build-layer
   make build
   make deploy
   ```

3. **Cambios en Código de Funciones**:
   ```bash
   make build
   make deploy
   ```

4. **Solución de Problemas**:
   ```bash
   make clean
   make install-deps
   make build-layer
   make build
   make deploy
   ```

### Notas Importantes

1. **Orden de Ejecución**:
   - Siempre construir la layer antes del build general
   - Limpiar antes de reconstruir si hay problemas
   - Instalar dependencias antes de construir

2. **GitHub Actions vs Local**:
   - GitHub Actions ejecuta los comandos automáticamente
   - Localmente se ejecutan manualmente según necesidad
   - Mismo resultado final en ambos casos

3. **Permisos y Configuración**:
   - Asegurar que AWS CLI está configurado localmente
   - Tener los permisos necesarios en AWS
   - Configurar variables de ambiente necesarias