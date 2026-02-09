# Source removal in `sources.py`


In this project, all available sources are defined in the `sources.py` file. This file contains the list of sources that the system can use for various purposes.

## File localization

The file is located at:
```
.src/sources.py
```

## Basic structure

Inside `sources.py`, the sources are organized as a list, for example:

```python
SOURCES = [
    "parlamento": ParlamentoDownloader,
    # ...
]
```

## How to remove a source

To remove an available source, follow these steps:

1. Open `sources.py` with your favorite code editor.
2. Locate the list of available sources (`SOURCES` in the example above).
3. Remove the entry corresponding to the source you want to delete.

For example, if you want to remove `"parlamento"`:

```python
SOURCES = [
    # ...
]
```
4. Delete the implementation file for the corresponding downloader (in this case, `"parlamento"`):
    ```
    .src/downloaders/parlamento.py
    ```

5. Save changes.

## Considerations

- After modifying `sources.py`, it is recommended to restart the application for the changes to take effect.
- The `config.py` file contains source-specific settings. Even if you remove a source from `sources.py`, these settings will still be present, though they won't cause any issues. It's important to be aware that they are there.
