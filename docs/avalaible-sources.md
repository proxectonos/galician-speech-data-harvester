# Eliminación de Fontes en `sources.py`

Neste proxecto, todas as fontes dispoñibles están definidas no arquivo `sources.py`. Este arquivo contén a lista de fontes que o sistema pode usar para distintos propósitos.

## Localización do arquivo

O arquivo atópase en:
```
.src/sources.py
```

## Estrutura básica

Dentro de `sources.py`, as fontes están organizadas como unha lista, por exemplo:

```python
SOURCES = [
    "parlamento": ParlamentoDownloader,
    # ...
]
```

## Como eliminar unha fonte

Para eliminar unha fonte dispoñible, segue estes pasos:

1. Abre `sources.py` co teu editor de código favorito.
2. Localiza a lista de fontes dispoñibles (`SOURCES` no exemplo anterior).
3. Elimina a entrada correspondente á fonte que desexas eliminar.

Por exemplo, se queres eliminar `"parlamento"`:

```python
SOURCES = [
    # ...
]
```
4. Elimina o archivo de implementación do downloader correspondente (Neste caso `"parlamento"`):
    ```
    .src/downloaders/parlamento.py
    ```


5. Garda os cambios.

## Consideracións

- Despois de modificar `sources.py`, é recomendable reiniciar a aplicación para que os cambios teñan efecto.
- No arquivo `config.py` hai configuracións específicas de cada fonte. Aínda que elimines unha fonte de `sources.py`, estas configuracións seguirán presentes aínda que non causarán problemas, é importante saber que existen alí.
