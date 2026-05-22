# Desde 0 pq me dio la gana, sapos

# 🎬 Uneflix

---

## Requisitos

- Python 3.10+
- pip

---

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/carlosalsa-py/uneflix2.git
cd uneflix
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

### 4. Aplicar migraciones

```bash
python manage.py migrate
```

### 5. Cargar películas y datos iniciales

```bash
python manage.py loaddata movies/fixtures/datos.json
```

### 6. Crear superusuario

```bash
python manage.py createsuperuser
```

### 7. Correr el servidor

```bash
python manage.py runserver
```

Entra a **http://127.0.0.1:8000**

Luego de hacer cambios en la base de datos correr python manage.py dumpdata movies --indent 2 --natural-foreign --natural-primary -o movies/fixtures/datos.json

---

## Notas importantes

- Las carpetas `media/posters/` y `media/backdrops/` deben existir antes de subir imágenes. Si no existen, créalas manualmente.
- Para agregar películas, géneros o gestionar usuarios: **http://127.0.0.1:8000/admin**
- El archivo `db.sqlite3` es local y no se comparte. Cada quien tiene su propia base de datos.
- Las imágenes están en la carpeta `media/`. Si no se ven los posters, verifica que esa carpeta esté en la raíz del proyecto.

---

## Estructura del proyecto

```
uneflix/
├── movies/                  → App de películas y series
│   ├── fixtures/
│   │   └── initial_data.json → Datos iniciales
│   ├── templates/movies/    → Templates HTML
│   ├── models.py            → Genre, Movie, Watchlist
│   ├── views.py             → Lógica de las páginas
│   └── urls.py              → Rutas de la app
├── users/                   → App de usuarios
│   ├── templates/users/     → Login y registro
│   ├── models.py            → Usuario personalizado
│   └── views.py             → Login, registro, logout
├── media/                   → Imágenes subidas
│   ├── posters/             → Posters de películas
│   └── backdrops/           → Imágenes de banner
└── uneflix/                 → Configuración del proyecto
    ├── settings.py
    └── urls.py
```

---

## Funcionalidades

- Registro e inicio de sesión
- Página principal con grid de películas y series
- Banner de película destacada
- Filtro por género sin recargar la página
- Página de detalle de cada película
- Watchlist personal por usuario
- Responsive (funciona en celular)
- Panel de administración

---

## Próximamente

- 🔜 Reproductor de video
- 🔜 Sistema de membresías
- 🔜 Calificaciones y comentarios
- 🔜 Perfiles de usuario
- 🔜 Base de datos en la nube

---
