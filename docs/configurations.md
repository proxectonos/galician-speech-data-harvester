# Scraping configuration

The config.py module defines the **general and specific configuration** for the project's scraping tools. Its purpose is to centralize all operating parameters: from download and audio options to per-source limits and logging settings.


## General file structure

The file contains:

1. **Basic and global settings** (user settings).
2. **Source-specific settings**.
3. **Helper functions** to initialize the logging system and HTTP headers.

## User-configurable part

The user can safely modify the following parameters:

### Adjustable Global Parameters

| Variable | Description | Default Value |
|-----------|-------------|-------------------|
| `WORKERS` | Number of simultaneous downloads.| `5` |
| `AUDIO_SAMPLE_RATE` | Audio sampling frequency (Hz). | `16000` |
| `AUDIO_CHANNELS` | Number of channels (1 = mono, 2 = stereo). | `1` |
| `AUDIO_FORMAT` | Audio output format. | `"wav"` |
| `DEFAULT_TIMEOUT` | Maximum waiting time in seconds. | `30` |
| `MAX_RETRIES` | Maximum number of retries if a download fails. | `3` |
| `CHUNK_SIZE` | Download fragment size in bytes. | `8192` |
| `DOWNLOADS_DIR` | Path where downloaded files are saved. | `./data/downloads` |
| `LOGS_DIR` | Path where log files are saved. | `./logs` |


---

### Specific source configuration

Each source has its own configuration block, where the **user can modify the limit date (`limit_date`)** up to which the scraping is desired.

Editable configuration per source example:

- **Galician Parliament**
  ```python
  "limit_date": datetime.strptime("2022-05-25", "%Y-%m-%d").date()
  ```


## User-unmodifiable part

The rest of the file contains **internal and critical** settings that should be changed with care as they affect the program's functionality (they ensure the scraper runs stably and efficiently):

1. **Scrapy and Twisted initialization**
   ```python
   asyncioreactor.install()
   configure_logging(install_root_handler=False)
   ```
   - Configure the Twisted reactor for asynchronous handling.
   - Adjust Scrapy's logging to avoid duplicates and excessive messages.
   - Modifying this can cause the scraping to fail or hang.

2. **Default HTTP headers and User-Agent**
   ```python
   DEFAULT_HEADERS, USER_AGENT
   ```
   - They ensure compatibility with web servers by simulating a real browser.
   - They maintain consistent behavior across all sources.
   - Changing them could cause sites to freeze or respond incorrectly.

3. **Source-specific settings not related to `limit_date` or exclusions**
   - Base URLs, search endpoints, session types, and internal prefixes.
   - These are necessary for the scraper to correctly identify content.
   - Modifying them can break data extraction.

4. **`yt-dlp` options for audio extraction and conversion**
   ```python
   YTDLP_OPTIONS
   ```
   - Defines the audio format, quality, and automatic conversions to `.wav`.
   - Ensures that all downloaded audio has the same quality and format.
   - Incorrect changes may result in incompatible files or errors during download.

5. **Logging funtions**
   ```python
   setup_logging, setup_root_logging
   ```
   - Manage logs in the console and in a file, recording scraper errors and events.  
   - Allow debugging issues without interrupting execution.  
   - Altering them could result in loss of error information or duplicate messages.

> **Recommendation:** Do not touch any other section that is not marked as configurable.
> Changing these blocks can cause **scraper crashes, data loss, or IP blocks**, affecting the project's stability.
