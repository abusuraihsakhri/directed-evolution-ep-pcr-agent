# Directed Evolution / Error-Prone PCR

### [Open the Live Application →](https://abusuraihsakhri.github.io/directed-evolution-ep-pcr-agent/)

A Python toolkit for conceptual error-prone PCR (ep-PCR), sequence mutation, library coverage and directed-evolution simulation, with a standalone browser calculator and a separate FastAPI audit service.

## Features

- **PCR mutation-rate estimate:** Illustrative dependence on MnCl₂, dNTP imbalance, Taq baseline error rate, cycle count and template length.
- **Mutation-count probabilities:** Poisson probability mass function, cumulative distribution and a tabulated distribution.
- **Variant coverage:** Expected library representation, screening-size estimates and diversity indices.
- **Sequence simulation:** Nucleotide substitutions, codon translation and synonymous/nonsynonymous/nonsense classifications.
- **Evolution simulation:** NK fitness landscapes and tournament or roulette selection.
- **Audit service:** Rule-based supervisory workers and an in-memory, HMAC-SHA256-linked audit ledger.
- **Browser interface:** Local mutation-rate, library-size and DNA simulation forms with JSON export, no server required.

### Scientific limitations

The MnCl₂/dNTP mutation-rate multipliers are **heuristic**, not experimental calibration curves. They should not be used to set wet-lab reaction conditions without independent validation. Library coverage uses an equal-probability occupancy model: actual libraries may show severe representation bias. Sequence simulation uses a per-site alteration probability of `1 − exp(−λ / sequence_length)`, an approximation for unique altered sites. The NK landscape is a generic mathematical model, not a trained predictor of protein fitness.

## Browser application

The static application is in [`web/`](web/). Open `web/index.html` in a modern browser, enter the parameters and run a calculation; results can be exported as JSON. It runs in JavaScript and does **not** load a Python runtime, use a backend, call third-party APIs or send sequence data off-device.

The `web/` directory is deployed to [GitHub Pages](https://abusuraihsakhri.github.io/directed-evolution-ep-pcr-agent/) through GitHub Actions. The deployment workflow verifies that the public page and JavaScript module are served successfully.

## Python installation

Python 3.9+ is declared; the CI matrix tests Python 3.10, 3.11 and 3.12.

```bash
git clone https://github.com/abusuraihsakhri/directed-evolution-ep-pcr-agent.git
cd directed-evolution-ep-pcr-agent
python -m pip install -e .
python cli.py --help
```

### Example commands

```bash
python cli.py rate --mncl2 0.1 --dntp-imbalance 1 --cycles 30 --length 1000 --json
python cli.py poisson --lambda-val 3 --max-k 15
python cli.py library --positions 4 --choices 4 --size 10000
python cli.py simulate --sequence ATGGCTGAA --lambda-val 2 --seed 42
python cli.py evolve --length 12 --generations 10 --population 100 --k 2 --seed 42
python cli.py audit --task-id EXAMPLE-1 --primary-metric 15 --json
python cli.py verify-audit --json
```

The `chat` command currently uses a deterministic mock response. It does not perform model-based scientific verification.

### API and Docker

```bash
python -m pip install -e ".[server]"
python -m uvicorn agents.api:app --host 127.0.0.1 --port 8000
# http://127.0.0.1:8000/docs and /health
```

Docker uses the same `agents.api:app` ASGI entry point. For container deployment, set a non-placeholder `AUDIT_SECRET_KEY` environment variable (for instance via a private environment or secret manager) and then run `docker compose up --build`. The ledger is **process-local and nonpersistent**, and the key must remain secret. HMAC verification detects modifications to stored, signed metadata; it is not a substitute for persistent authenticated audit storage.

**Security and privacy:** The browser version does not upload data. The API accepts requests without authentication and exposes in-memory audit metadata. Its identifier-pattern guard is not a complete PHI detector, nor does the application establish HIPAA, CAP, CLSI or ISO compliance. Do not send real patient identifiers or expose this API publicly without appropriate authentication, transport security, access controls and operational review.

## Tests

```bash
python -m pip install -e ".[server,dev]"
python -m pip check
python -m pytest -q
node --check web/app.mjs
node --test tests/web.test.mjs
```

Node.js is used only for browser-calculator tests. The runtime web application has no build step or external JavaScript dependencies.

## Technology and license

Standard-library Python numerical models, Pydantic 2, optional FastAPI/Uvicorn service, and vanilla HTML/CSS/JavaScript for the browser calculator. The interface targets modern desktop and mobile browsers with JavaScript modules enabled.

Licensed under the [MIT License](LICENSE).
