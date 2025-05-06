# AWS Lambda Project with SAM

Este proyecto demuestra cómo configurar múltiples funciones Lambda usando AWS SAM (Serverless Application Model) con una capa compartida de dependencias (Lambda Layer).

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
│   └── process_data/           # Segunda función Lambda
│       ├── app.py              # Código de la función
│       └── requirements.txt     # Dependencias específicas (si las hay)
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

### 2. Funciones Lambda

Cada función Lambda está configurada en `template.yaml` y usa la layer compartida:
```yaml
HelloWorldFunction:
  Type: AWS::Serverless::Function
  Properties:
    CodeUri: src/hello_world/
    Handler: app.lambda_handler
    Runtime: python3.11
    Layers:
      - !Ref CommonDependenciesLayer
```

### 3. GitHub Actions Workflow

El workflow (`.github/workflows/deploy-lambda.yml`) automatiza el despliegue:

1. Configura el entorno Python
2. Instala dependencias del sistema
3. Instala AWS SAM CLI
4. Construye la Lambda Layer
5. Configura credenciales AWS
6. Construye y despliega la aplicación

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
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`

## Endpoints API

1. Hello World Function
   - Path: `/hello`
   - Método: GET
   - Autenticación: Requiere Custom Authorizer
   - Retorna: Mensaje de saludo y timestamp

2. Process Data Function
   - Path: `/process`
   - Método: POST
   - Autenticación: Requiere Custom Authorizer
   - Retorna: Estadísticas de datos procesados

## Custom Authorizer

El proyecto utiliza un Custom Authorizer para proteger los endpoints de la API. Este autorizer valida los tokens JWT en las peticiones.

### Configuración del Authorizer

1. **Headers Requeridos**
   - Todas las peticiones deben incluir el header: `Authorization: Bearer <token>`

2. **Formato del Token**
   - El token debe ser un JWT válido
   - Debe contener los claims necesarios (sub, exp, iat)

3. **Implementación**
   - El authorizer está implementado en `src/authorizer/app.py`
   - Valida la estructura y firma del token
   - Genera una política IAM que permite o deniega el acceso

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