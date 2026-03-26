# Excalibur

```text
                /\
               /**\
              /****\
             /******\
            /********\
           /**********\
          /____  ____\
               ||
               ||
               ||
               ||
            ___||___
           /   ||   \
          /____||____\
               /\
              /  \
```

Knowledge-driven Nmap orchestration with Ansible and structured reporting.

## What It Does

Excalibur turns a Markdown knowledge base into reproducible Nmap runs.

1. Select a scan profile.
2. Extract Nmap commands from the local cheatsheet.
3. Build a readable Ansible playbook.
4. Run the scan.
5. Convert Nmap XML into structured JSON.
6. Enrich results with CVE lookups when requested.

The result is a much cleaner workflow than ad hoc shell history: repeatable, inspectable, and easy to containerize.

## Why This Version Is Better

- Local knowledge source, no runtime GitHub dependency
- Real multi-command CLI via [Excalibur.py](/Users/billard/Documents/ExegolSpector/Excalibur.py)
- Backward-compatible legacy entrypoint via [ExegolSpector.py](/Users/billard/Documents/ExegolSpector/ExegolSpector.py)
- Structured core package in [exegol_spector/](/Users/billard/Documents/ExegolSpector/exegol_spector)
- Optional CVE enrichment in [Modules/cve_search.py](/Users/billard/Documents/ExegolSpector/Modules/cve_search.py)
- Container-ready workflow through [Dockerfile](/Users/billard/Documents/ExegolSpector/Dockerfile) and [docker-compose.yml](/Users/billard/Documents/ExegolSpector/docker-compose.yml)

## Architecture

CLI layer:
- [excalibur/cli.py](/Users/billard/Documents/ExegolSpector/excalibur/cli.py)
- [excalibur/banner.py](/Users/billard/Documents/ExegolSpector/excalibur/banner.py)
- [Excalibur.py](/Users/billard/Documents/ExegolSpector/Excalibur.py)

Core engine:
- [exegol_spector/knowledge.py](/Users/billard/Documents/ExegolSpector/exegol_spector/knowledge.py)
- [exegol_spector/playbooks.py](/Users/billard/Documents/ExegolSpector/exegol_spector/playbooks.py)
- [exegol_spector/reports.py](/Users/billard/Documents/ExegolSpector/exegol_spector/reports.py)
- [exegol_spector/nmap_report.py](/Users/billard/Documents/ExegolSpector/exegol_spector/nmap_report.py)
- [exegol_spector/runner.py](/Users/billard/Documents/ExegolSpector/exegol_spector/runner.py)

Legacy extension points:
- [Modules/attack_orchestrator.py](/Users/billard/Documents/ExegolSpector/Modules/attack_orchestrator.py)
- [Modules/cve_search.py](/Users/billard/Documents/ExegolSpector/Modules/cve_search.py)

## CLI

List available profiles:

```bash
python3 Excalibur.py profiles
```

Check local prerequisites:

```bash
python3 Excalibur.py doctor
```

Generate a playbook without running it:

```bash
python3 Excalibur.py build --type basic --targets 127.0.0.1
```

Run a scan end-to-end:

```bash
python3 Excalibur.py run --type basic --targets 127.0.0.1
```

Convert an existing XML report:

```bash
python3 Excalibur.py report --xml-report artifacts/nmap_report.xml
```

Inspect a JSON report:

```bash
python3 Excalibur.py inspect --json-report artifacts/nmap_report.json
```

Legacy compatibility:

```bash
python3 ExegolSpector.py --type basic --targets 127.0.0.1 --dry-run
```

## Docker

Build the image:

```bash
docker build -t excalibur .
```

Run the CLI in a disposable container:

```bash
docker run --rm -it \
  -v "$(pwd)/artifacts:/opt/excalibur/artifacts" \
  excalibur profiles
```

Build a playbook from the container:

```bash
docker run --rm -it \
  -v "$(pwd)/artifacts:/opt/excalibur/artifacts" \
  excalibur build --type basic --targets 127.0.0.1
```

Run with Docker Compose:

```bash
docker compose run --rm excalibur profiles
docker compose run --rm excalibur build --type basic --targets 127.0.0.1
```

The container includes:
- Python 3.11
- `nmap`
- `ansible`
- `git`
- project Python dependencies

## Outputs

Generated artifacts are written to `artifacts/`:

- `nmap_playbook.yml`
- `nmap_report.xml`
- `nmap_report.json`
- `scan_metadata.json`
- `vulnerabilities_report.json`

## Local Development

Install Python dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Run tests:

```bash
PYTHONPYCACHEPREFIX=/tmp/pycache python3 -m unittest discover -s tests
```

Run syntax checks:

```bash
PYTHONPYCACHEPREFIX=/tmp/pycache python3 -m py_compile \
  Excalibur.py \
  ExegolSpector.py \
  excalibur/*.py \
  exegol_spector/*.py \
  Modules/attack_orchestrator.py \
  Modules/cve_search.py
```

## Current Limits

- The current Nmap cheatsheet does not yet cover every advertised profile.
- Several historical scripts under [Modules/](/Users/billard/Documents/ExegolSpector/Modules) remain outside the maintained core.
- Ansible is still the execution backbone. A future step would be packaging via `pyproject.toml` and shipping a native console entrypoint.
