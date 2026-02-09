# Configuracións para o scraping

O módulo config.py define a **configuración xeral e específica** para as ferramentas de scraping do proxecto.
O seu propósito é centralizar todos os parámetros de funcionamento: desde opcións de descarga e audio, ata límites por fonte e axustes de logging.


## Estrutura xeral do ficheiro

O ficheiro contén:

1. **Configuracións básicas e globais** (axustes de usuario).
2. **Configuracións específicas por fonte**.
3. **Funcións auxiliares** para inicializar o sistema de logging e cabeceiras HTTP.



## Parte configurable polo usuario

O usuario pode modificar con seguridade os seguintes parámetros:

### Parámetros globais axustables

| Variable | Descrición | Valor por defecto |
|-----------|-------------|-------------------|
| `WORKERS` | Número de descargas simultáneas. | `5` |
| `AUDIO_SAMPLE_RATE` | Frecuencia de mostrexo do audio (Hz). | `16000` |
| `AUDIO_CHANNELS` | Número de canles (1 = mono, 2 = estéreo). | `1` |
| `AUDIO_FORMAT` | Formato de saída do audio. | `"wav"` |
| `DEFAULT_TIMEOUT` | Tempo máximo de espera en segundos. | `30` |
| `MAX_RETRIES` | Número máximo de reintentos se falla unha descarga. | `3` |
| `CHUNK_SIZE` | Tamaño dos fragmentos de descarga en bytes. | `8192` |
| `DOWNLOADS_DIR` | Ruta onde se gardan os ficheiros descargados. | `./data/downloads` |
| `LOGS_DIR` | Ruta onde se gardan os ficheiros de log. | `./logs` |


---

### Configuración específica por fonte

Cada fonte ten o seu propio bloque de configuración, donde o **usuario pode modificar a data límite (`limit_date`)** ata a cal se desexa realizar o scraping.

Exemplos de configuración editable por fonte:

- **Parlamento de Galicia**
  ```python
  "limit_date": datetime.strptime("2022-05-25", "%Y-%m-%d").date()
  ```


## Parte non modificable polo usuario

O resto do ficheiro contén configuracións **internas e críticas** que deben ser cambiadas con coidado xa que afectan a funcionalidade do programa (encárganse de que o scraper funcione de maneira estable e eficiente):

1. **Inicialización de Scrapy e Twisted**
   ```python
   asyncioreactor.install()
   configure_logging(install_root_handler=False)
   ```
   - Configura o reactor de Twisted para o manexo asincrónico.
   - Axusta o logging de Scrapy para evitar duplicados e mensaxes excesivos.
   - Modificar isto pode provocar que o scraping falle ou se bloquee.

2. **Cabeceiras HTTP por defecto e User-Agent**
   ```python
   DEFAULT_HEADERS, USER_AGENT
   ```
   - Garantizan compatibilidade cos servidores web ao simular un navegador real.
   - Mantén un comportamento uniforme entre todas as fontes.
   - Cambialas podería provocar bloqueos ou respostas incorrectas dos sitios.

3. **Configuracións de cada fonte non relacionadas con `limit_date` ou exclusións**
   - URLs base, endpoints de busca, tipos de sesión e prefixos internos.
   - Son necesarias para que o scraper identifique correctamente os contidos.
   - Modificalas pode romper a extracción de datos.

4. **Opcións de `yt-dlp` para extracción e conversión de audio**
   ```python
   YTDLP_OPTIONS
   ```
   - Define o formato de audio, calidade e conversións automáticas a `.wav`.
   - Garantiza que todos os audios descargados teñan a mesma calidade e formato.
   - Cambios indebidos poden xerar ficheiros incompatibles ou erros durante a descarga.

5. **Funcións de logging**
   ```python
   setup_logging, setup_root_logging
   ```
   - Xestionan os logs en consola e en ficheiro, rexistrando erros e eventos do scraper.
   - Permiten depurar problemas sen interromper a execución.
   - Alteralas podería resultar en perda de información de erros ou duplicación de mensaxes.

> **Recomendación:** Non tocar ningunha outra sección que non estea marcada como configurable.
> Cambiar estes bloques pode causar **fallos no scraper, perda de datos ou bloqueos de IP**, afectando á estabilidade do proxecto.
