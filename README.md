![ALIA Project](https://langtech-bsc.gitbook.io/alia-kit/~gitbook/image?url=https%3A%2F%2F798406309-files.gitbook.io%2F%7E%2Ffiles%2Fv0%2Fb%2Fgitbook-x-prod.appspot.com%2Fo%2Fspaces%252Fk1rmBoGwZe21EgkVbqEr%252Fuploads%252FHG0Arow2kpc28XAmZ3s2%252FLOGOALIA_POS_COLOR.png%3Falt%3Dmedia%26token%3D7d7cc93d-8cac-408d-a950-f5c7d189192b&width=768&dpr=4&quality=100&sign=c610ba&sv=2)

# Galician Speech Data Harvester

A tool for downloading and organising audio and text data in Galician from various public sources.

## Objective

Facilitating the collection of Galician data for the development of speech technologies and natural language processing, focusing on:
- Automated download of multimedia content
- Extraction and cleaning of transcripts
- Structured organisation of data

## Data sources

### 1. Galician Parliament
- **Media library**: https://mediateca.parlamentodegalicia.gal/activity
- **Search engine**: https://www.es.parlamentodegalicia.es/Buscador/Xeral
- **Output**:
  - Session audio (WAV 16kHz)
  - Temporally aligned transcripts (STM)
  - Text-based session journals (PDF)
- **Session types**:
  - Plenary session: `DSPG_[Nº]_[DDMMAAAA].wav`
  - Comission: `CPG_[Nº]_[DDMMAAAA].wav`
  - Non permanent comission: `CPG_NP_[DDMMAAAA].wav`
  - Special non permanent comission: `CPG_ENP_[DDMMAAAA].wav`
  - Non permanent legislative comission: `CPG_PNL_[DDMMAAAA].wav`
  - Other: `PG_[SIGLAS]_[DDMMAAAA].wav`

## Instalation

### Requirements
- Python 3.13+
- ffmpeg
- Git

### Local installation
```bash
# Clone repo
git clone <repo-url>
cd galician-speech-data-harvester

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate    # Windows

# Install dependencies
pip install -r requirements.txt

# Make the scraper executable
chmod +x scraper
```

### Docker (Recommended for cross-platform consistency)

```bash
# Create folders (to avoid permission errors)
mkdir data logs

# Build image (once, or when code/dependencies change)
UID_GID="$(id -u):$(id -g)" docker compose build

# Interactive mode (recommended for executing multiple commands)
UID_GID="$(id -u):$(id -g)" docker compose run --rm scraper
# Inside the bash container:
#   scraper status
#   scraper fetch --source all
#   scraper download --source parliament
#   exit

# Execution of individual commands
UID_GID="$(id -u):$(id -g)" docker compose run --rm scraper help
UID_GID="$(id -u):$(id -g)" docker compose run --rm scraper status
```

**Notes on Docker:**
- **UID_GID="$(id -u):$(id -g)"**: Allows Docker to run as your normal user instead of using root.
- **Interactive mode**: Allows multiple commands to be run in a session without recreating the container.
- **Volumes**: The `data/` and `logs/` directories are mounted on the host, so downloads persist.
- **Reconstruction**: Only needed when the code or dependencies change.
- **Cross-platform**: Works identically on Windows, macOS, and Linux.

## Usage

### Main commands

```bash
# See help
./scraper help

# Search for new content
./scraper fetch --source all

# Download content
./scraper download --source parlamento

# View download status
./scraper status
```

### Filtering options

```bash
# By date
./scraper download --date-from 2024-01-01 --date-to 2024-12-31

# By specific source
./scraper download --source parlamento

# Force redownload
./scraper download --force

# Personalized output directory
./scraper download --output-dir /ruta/personalizada
```

### Configuration options
You can check all the options here:
```
./docs/configurations.md
```
You can see how to remove a source here:
```
./docs/avalaible-sources.md
```



## Project structure

```
scripts_descarga/
├── src/
│   ├── BaseDownloader.py          # Base class for downloaders
│   ├── config.py                  # Global configuration
│   ├── sources.py                 # Avaliable sources
│   ├── downloaders/
│   │   ├── parlamento.py          # Galician Parliament
│   └── utils/
│       ├── audio.py               # Audio processing
│       └── pdf.py                 # PDF processing
├── data/downloads/                # Downloaded data
├── logs/                          # Execution logs
├── docs/                          # Documentation
├── scraper                        # Command interface (executable)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Output format

- **Audio**: WAV, 16-bit, 16 kHz, mono
- **Text**: TXT with transcripts and documents

## Development

### Development tools

```bash
# Make sure you have the virtual environment activated
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate    # Windows

# Install development dependencies
pip install -r requirements-dev.txt

# Configure pre-commit hooks
pre-commit install

# Execute manual formatting
ruff format .

# Run manual linter
ruff check . --fix

# Run all hooks manually
pre-commit run --all-files
```

**Important**: Always activate the virtual environment (`source venv/bin/activate`) before working on the project. The pre-commit hooks will run automatically on each commit to ensure code quality.

### Adding new source

1. Create a new downloader in `src/downloaders/`
2. Inherit from `BaseDownloader`
3. Implement methods
4. Register in `scraper`


## Aknowledgements

This work is funded by the Ministerio para la Transformación Digital y de la Función Pública - Funded by EU – NextGenerationEU within the framework of the project Desarrollo de Modelos ALIA. (Esta publicación del proyecto Desarrollo de Modelos ALIA está financiada por el Ministerio para la Transformación Digital y de la Función Pública y por el Plan de Recuperación, Transformación y Resiliencia – Financiado por la Unión Europea – NextGenerationEU).

We would like to thank Merlin Software for the technical development of this tool.
