# Local Swagger UI Viewer

A zero-dependency desktop app that lets you preview any OpenAPI YAML/JSON file
in your browser — no internet, no Docker, no npm.

![screenshot](https://i.imgur.com/placeholder.png)

## Features

- Serves Swagger UI entirely from local files (no CDN)
- Supports `.yaml`, `.yml`, and `.json` OpenAPI specs
- Configurable host and port (default `127.0.0.1:8000`)
- Dark-themed GUI — starts the browser automatically
- Pure Python stdlib — nothing to install

## Requirements

| | |
|---|---|
| Python | ≥ 3.10 |
| Dependencies | none (tkinter ships with CPython) |

> **Linux users:** if tkinter is missing, install it with  
> `sudo apt install python3-tk` (Debian/Ubuntu) or the equivalent for your distro.

## Usage

```bash
python main.py
```

1. Click **📂 Select File** and pick your `.yaml` / `.yml` / `.json` spec.
2. Set **Host** and **Port** if needed (defaults: `127.0.0.1:8000`).
3. Click **▶ Start** — your browser opens automatically.
4. Click **■ Stop** to shut down the server.

## Project structure

```
swagger_viewer/
├── main.py          # application entry point
├── index.html       # Swagger UI shell page
├── src/
│   ├── css/
│   │   └── swagger-ui.css
│   └── js/
│       ├── swagger-ui-bundle.js
│       └── swagger-ui-standalone-preset.js
├── requirements.txt
└── README.md
```

`openapi.yaml` is written at runtime when you load a spec — it is git-ignored.

## How it works

`main.py` spins up Python's built-in `http.server` in a background thread,
serving the project directory. When you pick a spec file it is copied to
`openapi.yaml` at the project root, which `index.html` fetches as `/openapi.yaml`.

## License

MIT
