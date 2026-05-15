# Scripts ALIA para descarga de datos de voz en galego

Ferramenta para descargar e organizar datos de audio e texto en lingua galega de diversas fontes públicas.

## Obxectivo

Facilitar a recompilación de datos en galego para o desenvolvemento de tecnoloxías da fala e procesamento de linguaxe natural, centrándose en:
- Descarga automatizada de contido multimedia
- Extracción e limpeza de transcricións
- Organización estruturada dos datos

## Fontes de Datos

### 1. Parlamento de Galicia
- **Mediateca**: https://mediateca.parlamentodegalicia.gal/activity
- **Buscador**: https://www.es.parlamentodegalicia.es/Buscador/Xeral
- **Saída**:
  - Audio de sesións (WAV 16kHz)
  - Transcricións con aliñamento temporal (de STM)
  - Diarios de sesións en texto (de PDF)
- **Tipos de sesión**:
  - Pleno: `DSPG_[Nº]_[DDMMAAAA].wav`
  - Comisión: `CPG_[Nº]_[DDMMAAAA].wav`
  - Comisión non permanente: `CPG_NP_[DDMMAAAA].wav`
  - Comisión especial non permanente: `CPG_ENP_[DDMMAAAA].wav`
  - Comisión permanente non lexislativa: `CPG_PNL_[DDMMAAAA].wav`
  - Outros: `PG_[SIGLAS]_[DDMMAAAA].wav`

## Instalación

### Requisitos
- Python 3.13+
- ffmpeg
- Git

### Instalación local
```bash
# Clonar repositorio
git clone <repo-url>
cd scripts_descarga

# Crear e activar entorno virtual
python3 -m venv venv
source venv/bin/activate  # En Linux/Mac
# venv\Scripts\activate    # En Windows

# Instalar dependencias
pip install -r requirements.txt

# Facer o scraper executable
chmod +x scraper
```

### Docker (recomendado para consistencia multiplataforma)

```bash
# Crear carpetas (para evitar erros de permisos)
mkdir data logs

# Construír imaxe (unha vez, ou cando cambia o código/dependencias)
UID_GID="$(id -u):$(id -g)" docker compose build

# Modo interactivo (recomendado para executar múltiples comandos)
UID_GID="$(id -u):$(id -g)" docker compose run --rm scraper
# Dentro do contedor bash:
#   scraper status
#   scraper fetch --source all
#   scraper download --source parlamento
#   exit

# Execución de comandos individuais
UID_GID="$(id -u):$(id -g)" docker compose run --rm scraper help
UID_GID="$(id -u):$(id -g)" docker compose run --rm scraper status
```

**Notas sobre Docker:**
- **UID_GID="$(id -u):$(id -g)"**: Permite que Docker se execute co teu usuario normal en vez de usar root.
- **Modo interactivo**: Permite executar múltiples comandos nunha sesión sen recrear o contedor
- **Volumes**: Os directorios `data/` e `logs/` móntanse no host, polo que as descargas persisten
- **Reconstrución**: Só é necesaria cando cambia o código ou as dependencias
- **Multiplataforma**: Funciona idénticamente en Windows, macOS e Linux

## Uso

### Comandos principais

```bash
# Ver axuda
./scraper help

# Buscar contido novo
./scraper fetch --source all

# Descargar contido
./scraper download --source parlamento

# Ver estado das descargas
./scraper status
```

### Opcións de filtrado

```bash
# Por datas
./scraper download --date-from 2024-01-01 --date-to 2024-12-31

# Por fonte específica
./scraper download --source parlamento

# Forzar re-descarga
./scraper download --force

# Directorio de saída personalizado
./scraper download --output-dir /ruta/personalizada
```

### Opcións de configuración
Podes consultar todas as opcións aquí:
```
./docs/configurations.md
```
Podes ver como eliminar unha fonte dispoñible aqui:
```
./docs/avalaible-sources.md
```



## Estrutura do Proxecto

```
scripts_descarga/
├── src/
│   ├── BaseDownloader.py          # Clase base para downloaders
│   ├── config.py                  # Configuración global
│   ├── sources.py                 # Fontes dispoñibles
│   ├── downloaders/
│   │   ├── parlamento.py          # Parlamento de Galicia
│   └── utils/
│       ├── audio.py               # Procesamento de audio
│       └── pdf.py                 # Procesamento de PDFs
├── data/downloads/                # Datos descargados
├── logs/                          # Logs de execución
├── docs/                          # Documentación
├── scraper                        # Interface de comandos (executable)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Formato de Saída

- **Audio**: WAV, 16-bit, 16 kHz, mono
- **Texto**: TXT con transcricións e documentos

## Desenvolvemento

### Ferramentas de desenvolvemento

```bash
# Asegurarse de ter o entorno virtual activado
source venv/bin/activate  # En Linux/Mac
# venv\Scripts\activate    # En Windows

# Instalar dependencias de desenvolvemento
pip install -r requirements-dev.txt

# Configurar pre-commit hooks
pre-commit install

# Executar formateo manual
ruff format .

# Executar linter manual
ruff check . --fix

# Executar todos os hooks manualmente
pre-commit run --all-files
```

**Importante**: Sempre activar o entorno virtual (`source venv/bin/activate`) antes de traballar no proxecto. Os pre-commit hooks executaranse automaticamente en cada commit para garantir a calidade do código.

### Engadir nova fonte

1. Crear novo downloader en `src/downloaders/`
2. Herdar de `BaseDownloader`
3. Implementar métodos
4. Rexistrar en `scraper`

# Agradecementos

Esta publicación no marco do proxecto *Desarrollo de Modelos ALIA* está financiada polo Ministerio para a Transformación Dixital e da Función Pública e polo Plan de Recuperación, Transformación e Resiliencia — financiado pola Unión Europea – NextGenerationEU.

Queremos agradecer a Merlin Software polo desenvolvemento técnico desta ferramenta.
