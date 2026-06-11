# Uneflix

Plataforma de streaming de películas y series desarrollada con Django.

**Equipo:** Fabiola Andrade · Carlos Belmonte · Oliver Garcia · Carlos Salcedo

---

## Requisitos

- Python 3.10+
- pip

---

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/carlosalsa-py/uneflix2.git
cd uneflix2
```

### 2. Crear y activar el entorno virtual

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Mac/Linux:**
```bash
python -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```
### 4. Configurar variables de entorno

Este proyecto utiliza variables de entorno para los datos sensibles
(SECRET_KEY) y la configuración que cambia entre desarrollo y producción
(DEBUG, ALLOWED_HOSTS).

**a)** Copia el archivo de ejemplo a tu propio `.env`:

```bash
# Mac/Linux
cp .env.example .env

# Windows (CMD)
copy .env.example .env

# Windows (PowerShell)
Copy-Item .env.example .env
```

**b)** Genera una `SECRET_KEY` única para tu entorno:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copia el valor que imprime y pégalo en tu `.env`, en la línea `SECRET_KEY=`.

**c)** Abre tu `.env` y verifica que las otras variables estén configuradas
para desarrollo:

```
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
```

> ⚠️ **Importante:** el archivo `.env` contiene secretos y nunca debe
> subirse al repositorio. Ya está incluido en `.gitignore`.

### 5. Aplicar migraciones

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Cargar datos iniciales

```bash
python manage.py loaddata movies/fixtures/datos.json --exclude=movies.watchlist
```

### 7. Crear superusuario

```bash
python manage.py createsuperuser
```

### 8. Correr el servidor

```bash
python manage.py runserver
```

Entra a **http://127.0.0.1:8000**

Para ver desde otro dispositivo en la misma red:

```bash
python manage.py runserver 0.0.0.0:8000
```

Luego accede desde el celular con `http://<IP-de-tu-PC>:8000`

---

## Guardar cambios en la base de datos

```bash
python manage.py dumpdata movies --indent 2 --natural-foreign --natural-primary --exclude=movies.watchlist -o movies/fixtures/datos.json
```

---

## Notas importantes

- Las carpetas `media/posters/`, `media/backdrops/`, `media/videos/` y `media/avatars/` deben existir antes de subir archivos. Si no existen, créalas manualmente.
- Para agregar películas, activar membresías o gestionar usuarios: **http://127.0.0.1:8000/admin**
- El archivo `db.sqlite3` es local y no se comparte en el repositorio. Cada quien tiene su propia base de datos.
- Si no se ven los posters o videos, verifica que la carpeta `media/` esté en la raíz del proyecto.
- Para activar la membresía de un usuario: Admin → Memberships → seleccionar el registro → cambiar status a `active`.

---

## Estructura del proyecto

```
uneflix2/
├── movies/                      → App de películas, series, reviews
│   ├── fixtures/
│   │   └── datos.json           → Datos iniciales del catálogo
│   ├── templates/movies/        → Templates HTML
│   │   ├── home.html            → Página principal con carrusel y catálogo
│   │   ├── detail.html          → Detalle de película/serie con reviews
│   │   ├── player.html          → Reproductor de película
│   │   ├── episode_player.html  → Reproductor de episodio
│   │   ├── watchlist.html       → Lista personal del usuario
│   │   ├── membresias.html      → Comparación de planes
│   │   ├── pago.html            → Formulario de suscripción
│   │   ├── anuncio1.html        → Anuncio emergente 1
│   │   ├── anuncio2.html        → Anuncio emergente 2
│   │   └── anuncio3.html        → Anuncio emergente 3
│   ├── models.py                → Genre, Movie, Watchlist, Season, Episode, Review
│   ├── views.py                 → Lógica de todas las páginas
│   ├── urls.py                  → Rutas de la app
│   └── admin.py                 → Modelos registrados en el panel admin
├── users/                       → App de usuarios y membresías
│   ├── templates/users/         → Templates HTML
│   │   ├── login.html           → Inicio de sesión
│   │   ├── register.html        → Registro
│   │   ├── terms.html           → Términos y condiciones
│   │   ├── perfil.html          → Perfil público y privado
│   │   └── perfil_editar.html   → Editar nombre y avatar
│   ├── models.py                → Usuario (AbstractUser), Membership
│   ├── views.py                 → Login, registro, términos, perfil
│   ├── urls.py                  → Rutas de la app
│   └── admin.py                 → Modelos registrados en el panel admin
├── media/                       → Archivos subidos por el admin
│   ├── posters/                 → Imágenes de póster
│   ├── backdrops/               → Imágenes de banner
│   ├── videos/                  → Archivos de video MP4
│   └── avatars/                 → Fotos de perfil de usuarios
├── static/                      → Archivos estáticos del proyecto
│   └── images/                  → Logo, favicon, mascota (miku.png)
├── uneflix/                     → Configuración principal
│   ├── settings.py
│   └── urls.py
├── db.sqlite3                   → Base de datos local (no se sube al repo)
├── manage.py
└── requirements.txt
```

---

## Funcionalidades

### Catálogo y reproducción
- Página principal con carrusel de películas destacadas y filtro por género
- Detalle de película/serie con tráiler embebido (YouTube) y botón de reproducción
- Reproductor de video MP4 local
- Soporte para series con temporadas y episodios
- Sistema de anuncios emergentes al reproducir contenido (usuarios gratuitos)

### Usuarios y perfiles
- Registro con aceptación de términos y condiciones
- Inicio de sesión y cierre de sesión
- Perfil público (visible por todos) y perfil privado (solo el dueño)
- Edición de nombre de visualización y foto de perfil (solo usuarios de pago)
- Watchlist personal — agregar y quitar contenido con un clic

### Sistema de membresías
| Plan | Código | Precio | Acceso |
|---|---|---|---|
| Unefista | `free` | Gratis | Contenido básico + anuncios |
| Cinéfilo | `medium` | $2.99/mes | Catálogo completo sin anuncios |
| Zerpanito | `zerpanito` | $4.99/mes | Todo + 3 pantallas simultáneas |

- Control de acceso por tier: cada contenido tiene un nivel requerido (`free`, `medium`, `premium`)
- El contenido bloqueado muestra un candado con el plan requerido
- Las membresías se activan manualmente desde el panel de administración

### Reviews y calificaciones
- Usuarios Cinéfilo y Zerpanito pueden dejar reseñas (1-5 estrellas + comentario)
- Usuarios gratuitos pueden leer reseñas pero no escribirlas
- Cada usuario puede tener una sola reseña por película (editable)
- Promedio de calificaciones visible en el detalle de cada película
- Las reseñas aparecen en el perfil del usuario

### Chatbot
- Miku Unefista: asistente virtual con respuestas predeterminadas sobre planes, métodos de pago y preguntas frecuentes

---

## Métodos de pago aceptados

- ✅ Tarjeta internacional (disponible)
- 🕐 Pago móvil (próximamente)
- 🕐 Transferencia bancaria (próximamente)

> El procesamiento de pago actual es simulado. Las membresías se activan manualmente por el administrador.

---
