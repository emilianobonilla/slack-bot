# Configuración de Slack Bot

Esta guía te ayudará a configurar tu bot de Slack desde cero hasta tenerlo funcionando en desarrollo y producción.

## 📋 Prerrequisitos

- Una cuenta de Slack con permisos para crear apps
- Python 3.8+ instalado
- Azure account (opcional, para producción)

## 🚀 Paso 1: Crear la App de Slack

### 1.1 Ir al Portal de Slack API

1. Ve a [https://api.slack.com/apps](https://api.slack.com/apps)
2. Haz clic en "Create New App"
3. Selecciona "From scratch"
4. Asigna un nombre a tu app (ej: "Mi Bot de Slack")
5. Selecciona el workspace donde quieres instalar el bot

### 1.2 Configurar Permisos del Bot

1. En la página de tu app, ve a **"OAuth & Permissions"** en el menú lateral
2. Scrollea hasta **"Scopes"** → **"Bot Token Scopes"**
3. Agrega los siguientes scopes:

**Scopes requeridos:**
- `app_mentions:read` - Para responder cuando mencionen al bot
- `channels:history` - Para leer mensajes en canales
- `chat:write` - Para enviar mensajes
- `commands` - Para manejar slash commands
- `im:history` - Para leer mensajes directos
- `im:write` - Para enviar mensajes directos
- `reactions:read` - Para leer reacciones
- `users:read` - Para obtener información de usuarios

**Scopes opcionales (según necesidades):**
- `channels:read` - Para obtener información de canales
- `groups:history` - Para leer mensajes en grupos privados
- `groups:write` - Para enviar mensajes en grupos privados
- `team:read` - Para obtener información del equipo

### 1.3 Instalar la App en tu Workspace

1. Después de agregar los scopes, scroll hacia arriba en la misma página
2. Haz clic en **"Install to Workspace"**
3. Autoriza la aplicación
4. **¡IMPORTANTE!** Copia el **"Bot User OAuth Token"** que empieza con `xoxb-`

### 1.4 Obtener el Signing Secret

1. Ve a **"Basic Information"** en el menú lateral
2. En la sección **"App Credentials"**, copia el **"Signing Secret"**

### 1.5 Configurar Socket Mode (Para Desarrollo)

1. Ve a **"Socket Mode"** en el menú lateral
2. Activa **"Enable Socket Mode"**
3. Crea un token de nivel de app:
   - Haz clic en "Generate Token and Scopes"
   - Nombre: "socket-mode-token"
   - Scopes: `connections:write`
4. **¡IMPORTANTE!** Copia el **"App-Level Token"** que empieza con `xapp-`

### 1.6 Configurar Event Subscriptions

1. Ve a **"Event Subscriptions"** en el menú lateral
2. Activa **"Enable Events"**
3. Si usas Socket Mode, no necesitas URL
4. En **"Subscribe to bot events"**, agrega:
   - `app_mention` - Cuando mencionen al bot
   - `message.im` - Mensajes directos
   - `reaction_added` - Reacciones agregadas
   - `team_join` - Nuevos miembros

### 1.7 Configurar Slash Commands (Opcional)

1. Ve a **"Slash Commands"** en el menú lateral
2. Haz clic en **"Create New Command"**
3. Configura los siguientes comandos:

**Comando /hello:**
- Command: `/hello`
- Request URL: (vacío si usas Socket Mode)
- Short Description: "Saluda al bot"
- Usage Hint: `[mensaje opcional]`

**Comando /info:**
- Command: `/info`
- Request URL: (vacío si usas Socket Mode)
- Short Description: "Información del bot"

**Comando /help:**
- Command: `/help`
- Request URL: (vacío si usas Socket Mode)
- Short Description: "Ayuda del bot"

## 🔧 Paso 2: Configurar el Entorno de Desarrollo

### 2.1 Configurar Variables de Entorno

1. Copia el archivo template:
```bash
cp .env.template .env
```

2. Edita el archivo `.env` con tus tokens:
```bash
# Reemplaza con tus tokens reales
SLACK_BOT_TOKEN=xoxb-your-actual-bot-token
SLACK_SIGNING_SECRET=your-actual-signing-secret
SLACK_APP_TOKEN=xapp-your-actual-app-token
SLACK_SOCKET_MODE=true
```

### 2.2 Instalar Dependencias

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
source venv/bin/activate  # En macOS/Linux
# o
venv\Scripts\activate     # En Windows

# Instalar dependencias
pip install -r requirements.txt
```

### 2.3 Probar la Configuración

```bash
# Ejecutar el bot en modo desarrollo
python -m src.app

# O directamente:
python src/app.py
```

Si todo está configurado correctamente, verás:
```
Starting Slack bot app_name=SlackBot version=1.0.0
Running in Socket Mode (development)
⚡️ Bolt app is running!
```

## 🧪 Paso 3: Probar el Bot

### 3.1 Pruebas Básicas

1. **Mencionar al bot:** En cualquier canal, escribe `@NombreDeTuBot hola`
2. **Mensaje directo:** Envía un DM al bot con "hola"
3. **Slash commands:** Prueba `/hello`, `/info`, `/help`

### 3.2 Verificar Logs

El bot mostrará logs estructurados en la consola:
```
Processing Slack event event_type=app_mention user_id=U1234567
Responded to app mention user_id=U1234567 channel_id=C1234567
```

## 🌐 Paso 4: Configuración para Producción (Azure Functions)

### 4.1 Preparar Azure Functions

1. Instala Azure Functions Core Tools:
```bash
npm install -g azure-functions-core-tools@4 --unsafe-perm true
```

2. Copia la configuración local:
```bash
cp local.settings.json.template local.settings.json
```

3. Edita `local.settings.json` con tus tokens reales

### 4.2 Probar Localmente con Azure Functions

```bash
func start
```

### 4.3 Configurar para HTTP Mode (Producción)

1. En tu app de Slack, ve a **"Socket Mode"**
2. **Desactiva Socket Mode**
3. Ve a **"Event Subscriptions"**
4. Configura la Request URL: `https://tu-function-app.azurewebsites.net/api/slack/events`

### 4.4 Desplegar a Azure

```bash
func azure functionapp publish <nombre-de-tu-function-app>
```

## 🔍 Solución de Problemas

### Error: "Configuration validation failed"

Verifica que todas las variables de entorno estén configuradas correctamente:
```bash
python -c "from src.config import validate_configuration; print(validate_configuration())"
```

### Error: "Failed to start Slack bot"

1. Verifica que los tokens sean correctos
2. Asegúrate de que Socket Mode esté habilitado (desarrollo)
3. Revisa que los scopes estén configurados

### El bot no responde a menciones

1. Verifica que el bot esté en el canal
2. Revisa los event subscriptions en Slack
3. Confirma que el scope `app_mentions:read` esté agregado

### Slash commands no funcionan

1. Verifica que los comandos estén creados en Slack
2. Si usas HTTP mode, configura las URLs correctas
3. Revisa que el scope `commands` esté agregado

## 📝 Comandos de Desarrollo

```bash
# Ejecutar el bot
python -m src.app

# Ejecutar tests (cuando estén implementados)
pytest

# Linting
flake8 src/
black src/
isort src/

# Azure Functions local
func start
```

## 🔒 Seguridad

- **Nunca** commitees tokens reales al repositorio
- Usa variables de entorno para todos los secretos
- En producción, usa Azure Key Vault o similar
- Verifica siempre las signatures de Slack

## 📚 Recursos Adicionales

- [Slack API Documentation](https://api.slack.com/)
- [Slack Bolt Framework](https://slack.dev/bolt-python/tutorial/getting-started)
- [Azure Functions Python Guide](https://docs.microsoft.com/en-us/azure/azure-functions/functions-reference-python)

---

¡Tu bot de Slack está listo! 🎉
