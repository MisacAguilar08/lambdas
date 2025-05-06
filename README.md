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
   - Retorna: Mensaje de saludo y timestamp

2. Process Data Function
   - Path: `/process`
   - Método: POST
   - Retorna: Estadísticas de datos procesados

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