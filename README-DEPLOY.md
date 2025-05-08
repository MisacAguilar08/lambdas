# 🚀 Guía de Despliegue con GitHub Actions

Este documento detalla la configuración y funcionamiento del pipeline de CI/CD implementado en `.github/workflows/deploy-lambda.yml`.

## 📋 Índice
- [Configuración Inicial](#configuración-inicial)
- [Estructura del Workflow](#estructura-del-workflow)
- [Triggers](#triggers)
- [Variables y Secretos](#variables-y-secretos)
- [Pasos del Pipeline](#pasos-del-pipeline)
- [Solución de Problemas](#solución-de-problemas)

## 🔧 Configuración Inicial

### Pre-requisitos

1. Cuenta de AWS con:
   - Access Key ID
   - Secret Access Key
   - Permisos para:
     - CloudFormation
     - Lambda
     - API Gateway
     - IAM
     - S3

2. Repositorio GitHub con:
   - Acceso a GitHub Actions
   - Secretos configurados
   - Permisos de workflow

### Estructura del Proyecto
```
.
├── .github/
│   └── workflows/
│       └── deploy-lambda.yml
├── src/
│   ├── authorizer/
│   └── token_generator/
├── layers/
│   ├── python/
│   └── requirements.txt
└── template.yaml
```

## 🏗️ Estructura del Workflow

### Nombre y Descripción
```yaml
name: Deploy Lambda
```
Define el nombre del workflow en la interfaz de GitHub Actions.

### Triggers Configurados

#### Push a Main
```yaml
on:
  push:
    branches:
      - main
    paths:
      - 'src/**'
      - 'layers/**'
      - 'template.yaml'
```
- Se activa al hacer push a main
- Solo en cambios en código o configuración
- Ignora cambios en documentación

#### Pull Requests
```yaml
  pull_request:
    branches:
      - main
    paths:
      - 'src/**'
      - 'layers/**'
      - 'template.yaml'
```
- Verifica cambios antes de merge
- Valida la construcción
- Previene problemas en main

#### Releases
```yaml
  release:
    types: [created]
```
- Activa despliegue en nuevos releases
- Versiona la aplicación
- Automatiza publicación

#### Manual Trigger
```yaml
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to deploy to'
        required: true
        default: 'dev'
        type: choice
        options:
          - dev
          - staging
          - prod
      debug:
        description: 'Enable debug logging'
        required: false
        type: boolean
        default: false
```
- Permite despliegue manual
- Selección de ambiente
- Opción de debug

## 🔐 Variables y Secretos

### Secretos Requeridos

1. AWS_ACCESS_KEY_ID
```yaml
aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
```
- Credencial de acceso AWS
- Debe tener permisos suficientes
- No compartir entre ambientes

2. AWS_SECRET_ACCESS_KEY
```yaml
aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
```
- Clave secreta AWS
- Rotar regularmente
- Mantener seguro

3. AWS_REGION
```yaml
aws-region: ${{ secrets.AWS_REGION }}
```
- Región de despliegue
- Consistente por ambiente
- Ejemplo: us-east-1

4. AUTH_TOKEN_SECRET
```yaml
AuthTokenSecret: ${{ secrets.AUTH_TOKEN_SECRET }}
```
- Secreto para JWT
- Mínimo 6 caracteres
- Único por ambiente

## 📦 Pasos del Pipeline

### 1. Checkout del Código
```yaml
- uses: actions/checkout@v3
```
**Propósito**: Obtener código del repositorio
**Configuración**: Usa versión 3 del action
**Resultado**: Código listo para build

### 2. Setup Python
```yaml
- name: Set up Python
  uses: actions/setup-python@v4
  with:
    python-version: '3.11'
    cache: 'pip'
```
**Propósito**: Preparar ambiente Python
**Configuración**:
- Python 3.11
- Cache de pip habilitado
**Resultado**: Ambiente Python listo

### 3. Dependencias del Sistema
```yaml
- name: Install system dependencies
  run: |
    sudo apt-get update
    sudo apt-get install -y build-essential python3-dev tree
```
**Propósito**: Instalar herramientas necesarias
**Paquetes**:
- build-essential: Compilación
- python3-dev: Headers Python
- tree: Visualización de estructura

### 4. AWS SAM CLI
```yaml
- name: Install AWS SAM CLI and build tools
  run: |
    python -m pip install --upgrade pip
    python -m pip install --upgrade setuptools wheel
    python -m pip install aws-sam-cli
```
**Propósito**: Instalar herramientas AWS
**Componentes**:
- pip actualizado
- setuptools y wheel
- AWS SAM CLI

### 5. Verificación de Estructura
```yaml
- name: Verify Project Structure
  run: |
    echo "Verificando estructura del proyecto..."
    if [ ! -d "layers" ]; then
      echo "Error: Directorio 'layers' no encontrado"
      exit 1
    fi
    if [ ! -d "layers/python" ]; then
      echo "Creando directorio layers/python..."
      mkdir -p layers/python
    fi
    if [ ! -f "layers/requirements.txt" ]; then
      echo "Error: Archivo layers/requirements.txt no encontrado"
      exit 1
    fi
    echo "Estructura del proyecto:"
    tree -a -I '.git|.aws-sam'
```
**Propósito**: Validar estructura del proyecto
**Verificaciones**:
- Existencia de directorios
- Archivos requeridos
- Estructura correcta

### 6. Build de Layer
```yaml
- name: Build Lambda Layer
  run: |
    echo "Building Lambda Layer..."
    pip install -r layers/requirements.txt -t layers/python/
    if [ -f "Makefile" ]; then
      make build-layer
    fi
```
**Propósito**: Construir Lambda Layer
**Proceso**:
- Instalar dependencias
- Ejecutar build personalizado
- Preparar para deployment

### 7. Credenciales AWS
```yaml
- name: Configure AWS Credentials
  uses: aws-actions/configure-aws-credentials@v1
  with:
    aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
    aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    aws-region: ${{ secrets.AWS_REGION }}
```
**Propósito**: Configurar acceso AWS
**Configuración**:
- Credenciales seguras
- Región específica
- Acceso temporal

### 8. Limpieza de Stack
```yaml
- name: Check and Delete Failed Stack
  run: |
    if aws cloudformation describe-stacks --stack-name lambdas-init 2>/dev/null | grep -q 'ROLLBACK_COMPLETE'; then
      echo "Deleting failed stack..."
      aws cloudformation delete-stack --stack-name lambdas-init
      aws cloudformation wait stack-delete-complete --stack-name lambdas-init
    fi
```
**Propósito**: Limpiar recursos fallidos
**Proceso**:
- Verificar estado
- Eliminar si fallido
- Esperar limpieza

### 9. SAM Build
```yaml
- name: SAM Build
  run: |
    echo "Running SAM build..."
    sam build --use-container
    echo "SAM build complete. Contents of .aws-sam:"
    ls -la .aws-sam/
```
**Propósito**: Construir aplicación
**Configuración**:
- Uso de contenedores
- Build aislado
- Verificación de outputs

### 10. SAM Deploy
```yaml
- name: SAM Deploy
  run: |
    sam deploy \
      --template-file .aws-sam/build/template.yaml \
      --stack-name lambdas-init \
      --no-confirm-changeset \
      --no-fail-on-empty-changeset \
      --force-upload \
      --no-progressbar \
      --capabilities CAPABILITY_IAM \
      --region "${{ secrets.AWS_REGION }}" \
      --resolve-s3 \
      --parameter-overrides "AuthTokenSecret=${{ secrets.AUTH_TOKEN_SECRET }}"
```
**Propósito**: Desplegar aplicación
**Configuración**:
- Template compilado
- Stack name fijo
- Creación automática S3
- Parámetros override

## 🔍 Solución de Problemas

### Errores Comunes

1. Fallo de Credenciales
```bash
# Verificar configuración
aws configure list
aws sts get-caller-identity
```
**Solución**:
- Verificar secretos en GitHub
- Validar permisos IAM
- Comprobar región

2. Error de Build
```bash
# Limpiar y reconstruir
rm -rf .aws-sam/
sam build --debug
```
**Solución**:
- Limpiar cache
- Verificar dependencias
- Revisar logs

3. Fallo de Deployment
```bash
# Ver eventos del stack
aws cloudformation describe-stack-events \
  --stack-name lambdas-init
```
**Solución**:
- Revisar eventos CloudFormation
- Verificar permisos
- Validar template

### Verificaciones

1. Estado del Stack
```bash
aws cloudformation describe-stacks \
  --stack-name lambdas-init \
  --query 'Stacks[0].StackStatus'
```

2. Recursos Creados
```bash
aws cloudformation list-stack-resources \
  --stack-name lambdas-init
```

3. Outputs
```bash
aws cloudformation describe-stacks \
  --stack-name lambdas-init \
  --query 'Stacks[0].Outputs'
```

## 📝 Notas Adicionales

### Mejores Prácticas

1. Versionamiento
- Usar tags semánticos
- Documentar cambios
- Mantener changelog

2. Seguridad
- Rotar credenciales
- Mínimos permisos
- Revisar secretos

3. Monitoreo
- Revisar logs
- Configurar alertas
- Documentar errores

### Mantenimiento

1. Actualizaciones
- Mantener dependencias al día
- Actualizar runtime
- Revisar deprecated features

2. Limpieza
- Eliminar recursos no usados
- Limpiar buckets S3
- Archivar logs antiguos

3. Documentación
- Mantener README actualizado
- Documentar cambios
- Actualizar diagramas