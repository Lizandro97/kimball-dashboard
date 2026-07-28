# Superstore BI Dashboard

Dashboard analítico para la cadena de suministro Superstore, construido con
**FastAPI** + **Plotly** + **PostgreSQL** siguiendo la metodología **Kimball DW/BI**.

## Stack

| Capa       | Tecnología                     |
| ---------- | ------------------------------ |
| Backend    | Python 3.13, FastAPI, Uvicorn  |
| Frontend   | HTML, CSS, JavaScript (SPA)    |
| BD         | PostgreSQL 16                  |
| Charts     | Plotly.js                      |
| ETL        | Pandas, SQLAlchemy             |
| Export     | OpenPyXL (Excel `.xlsx`)       |

## Requisitos

- [Docker Desktop](https://docs.docker.com/desktop/setup/install/windows-install/)
  (incluye Docker Compose)

## Cómo levantar

```powershell
# 1. Clonar el repositorio
git clone <url-del-repo>
cd Superstore/dashboard

# 2. Iniciar todo (PostgreSQL + dashboard + ETL automático)
docker compose up
```

El primer arranque:
1. Construye la imagen del dashboard
2. Crea el contenedor de PostgreSQL
3. Ejecuta el pipeline ETL (extrae el CSV `data/super-store.csv`, transforma y carga las dimensiones y la tabla de hechos)
4. Inicia el servidor en `http://localhost:8000`

Las ejecuciones siguientes solo levantan los contenedores existentes (los datos persisten en un volumen Docker). La ETL solo se ejecuta al construir la imagen por primera vez o si se fuerza la recreación.

### Comandos útiles

```powershell
# Iniciar en segundo plano (detached)
docker compose up -d

# Ver logs
docker compose logs -f

# Detener contenedores (los datos persisten)
docker compose down

# Detener y borrar los datos (vuelve a estado inicial)
docker compose down -v

# Reconstruir la imagen tras cambios
docker compose build
```

## Arquitectura del proyecto

```
Superstore/dashboard/
├── data/
│   └── super-store.csv        # Dataset CSV original
├── db/
│   ├── schema.sql             # DDL de referencia
│   ├── engine.py              # Conexión a PostgreSQL (singleton)
│   └── models.py              # Modelos ORM SQLAlchemy
├── etl/
│   ├── run.py                 # Orquestador
│   ├── extract.py             # Extracción CSV → raw
│   ├── transform.py           # Limpieza y transformaciones
│   └── load.py                # Carga dimensional + fact table
├── src/
│   ├── api/
│   │   ├── app.py             # FastAPI app + lifespan
│   │   ├── routes/            # Endpoints: overview, sales, profitability, customers, shipping, export
│   │   └── services/          # Lógica de negocio + gráficos
│   ├── components/
│   │   └── charts.py          # Funciones de generación de gráficos Plotly
│   └── static/
│       ├── index.html         # SPA
│       ├── css/style.css      # Estilos
│       └── js/                # app.js (controlador SPA), render.js (Plotly), api.js (fetch)
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

## Ejecución local (sin Docker)

Si prefieres ejecutar sin Docker (solo Linux/macOS):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tu conexión PostgreSQL

# Crear base de datos y cargar datos
python -m etl.run

# Iniciar servidor
uvicorn src.api.app:app --host 0.0.0.0 --port 8000
```

## Módulos del dashboard

| Ruta              | Módulo            | KPIs principales               |
| ----------------- | ----------------- | ------------------------------ |
| `/`               | Overview          | Ventas totales, profit, órdenes |
| `/ventas`         | Ventas            | Ventas por categoría, tendencias |
| `/rentabilidad`   | Rentabilidad      | Profit por producto/región      |
| `/clientes`       | Clientes          | Top clientes, segmentación      |
| `/envios`         | Envíos            | Ship modes, tiempos de entrega  |

Cada módulo incluye filtros (Región, Año, Segmento) y exportación a Excel.