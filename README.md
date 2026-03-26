# Excalibur

[![Python](https://img.shields.io/badge/python-3.9%2B-3776AB.svg)](#local-development)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![CLI](https://img.shields.io/badge/interface-CLI-black.svg)](#cli)
[![Docker](https://img.shields.io/badge/runtime-Docker-2496ED.svg)](#docker)

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

## Overview

Excalibur turns a local Markdown knowledge base into reproducible Nmap runs:

1. pick a scan profile
2. extract `nmap` commands from the knowledge file
3. generate a readable Ansible playbook
4. run the scan
5. convert Nmap XML into structured JSON
6. optionally enrich the report with CVE lookups

The goal is simple: make scanning workflows easier to inspect, easier to repeat, and much easier to ship in a clean container.

## Highlights

- multi-command CLI with profile discovery, build, run, report, inspect, and doctor workflows
- startup banner and installable `excalibur` command
- local knowledge source, no runtime GitHub fetch dependency
- structured core modules instead of a single monolithic script
- backward-compatible legacy entrypoint via [ExegolSpector.py](/Users/billard/Documents/ExegolSpector/ExegolSpector.py)
- container-ready execution via [Dockerfile](/Users/billard/Documents/ExegolSpector/Dockerfile)

## Architecture

Product-facing CLI:
- [Excalibur.py](/Users/billard/Documents/ExegolSpector/Excalibur.py)
- [excalibur/cli.py](/Users/billard/Documents/ExegolSpector/excalibur/cli.py)
- [excalibur/banner.py](/Users/billard/Documents/ExegolSpector/excalibur/banner.py)

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
excalibur profiles
```

Validate local prerequisites:

```bash
excalibur doctor
```

Generate a playbook without executing it:

```bash
excalibur build --type basic --targets 127.0.0.1
```

Run a scan end-to-end:

```bash
excalibur run --type basic --targets 127.0.0.1
```

Convert an existing XML report:

```bash
excalibur report --xml-report artifacts/nmap_report.xml
```

Inspect a JSON report:

```bash
excalibur inspect --json-report artifacts/nmap_report.json
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

Use Compose:

```bash
docker compose run --rm excalibur profiles
docker compose run --rm excalibur build --type basic --targets 127.0.0.1
```

The image includes:
- Python 3.11
- `nmap`
- `ansible`
- `git`
- the installed `excalibur` entrypoint

## Installation

Local editable install:

```bash
python3 -m pip install -e .
```

Classic dependency install:

```bash
python3 -m pip install -r requirements.txt
```

Version check:

```bash
excalibur --version
```

## Outputs

Generated artifacts are written to `artifacts/`:

- `nmap_playbook.yml`
- `nmap_report.xml`
- `nmap_report.json`
- `scan_metadata.json`
- `vulnerabilities_report.json`

## Local Development

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

- the current Nmap cheatsheet does not yet cover every advertised profile
- several historical scripts under [Modules/](/Users/billard/Documents/ExegolSpector/Modules) remain outside the maintained core
- Ansible is still the execution backbone; a future step could be richer profile schemas and more structured execution backends
