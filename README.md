# Directed Evolution Ep PCR Agent

> **Domain:** Protein Engineering & Directed Evolution
> **Standards:** CAP / CLSI / ISO Quality Frameworks

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

**Directed Evolution Ep PCR Agent** is a precision computational engine for error-prone PCR (ep PCR) and directed evolution workflows. It provides:

- **Mutation Rate Calculation**: Models MnCl2 concentration, dNTP imbalance, and cycle effects on Taq polymerase error rates
- **Poisson Distribution Analysis**: Probability distributions for mutation counts
- **Library Size Estimation**: Coverage calculations for variant libraries
- **Mutation Simulation**: In silico ep PCR with codon translation and mutation classification
- **Directed Evolution Simulation**: NK fitness landscape modeling with tournament/roulette selection
- **Distributed Component Audit**: Multi-worker consensus system with HMAC-SHA256 tamper-evident audit trail
- **Zero-PHI Guard**: Active pattern detection blocking SSNs, MRNs, phone numbers, and patient identifiers

---

## ⚙️ Key Capabilities & Algorithmic Modules

### Core Engine (`directed_evolution/`)
- **Deterministic Calculation Engine**: Mutation rate modeling based on PCR conditions
- **Poisson Distribution**: P(k) = e^(-λ) × λ^k / k! with cumulative distribution
- **Library Diversity**: Shannon entropy and Simpson's diversity indices
- **NK Fitness Landscape**: Epistatic interactions model for genotype-phenotype mapping
- **Selection Pressure**: Tournament and roulette wheel selection strategies

### Distributed Component System (`agents/`)
- **Multi-Worker Consensus**: InvariantQC, SafetyEscalation, ProtocolConformance workers
- **Risk & Urgency Classification**: ROUTINE / ELEVATED_RISK / CRITICAL_STAT_PANIC tiers
- **HMAC-SHA256 Audit Trail**: Chained, cryptographically signed logs for every evaluation
- **Zero-PHI Outbound Interceptor**: AST and regex inspection blocking sensitive identifiers

### Enrichment Suite (`enrichment.py`)
- Error Rate Calibration & Mutation Spectrum Modeling
- Library Diversity Analysis & Representation Assessment
- Functional Variant Enrichment Strategies
- DNA Shuffling & Stochastic Recombination Planning
- Machine Learning-Directed Evolution Cycles
- Structural Context Analysis for Variant Prioritization
- High-Throughput Sequencing & Variant Calling
- Multi-Parameter Optimization & Balancing

---

## 💻 Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/directed-evolution-ep-pcr-agent.git
cd directed-evolution-ep-pcr-agent

# Install dependencies
pip install -e .

# For development (includes testing)
pip install -e ".[dev]"
```

---

## 💻 CLI Quickstart & Usage

### 1. Mutation Rate Analysis
```bash
python cli.py rate --mncl2 0.5 --dntp-imbalance 1.0 --cycles 30 --length 1000
python cli.py rate --mncl2 0.5 --cycles 30 --length 1000 --json
```

### 2. Poisson Distribution
```bash
python cli.py poisson --lambda-val 3.0 --max-k 15
python cli.py poisson --lambda-val 5.0 --json
```

### 3. Library Size Estimation
```bash
python cli.py library --positions 5 --choices 20
python cli.py library --positions 8 --size 10000 --json
```

### 4. Mutation Simulation
```bash
python cli.py simulate --sequence ATGCGATCGATCG --lambda-val 2.0 --seed 42
python cli.py simulate --sequence ATGCGATCGATCG --lambda-val 1.0 --json
```

### 5. Directed Evolution Simulation
```bash
python cli.py evolve --length 20 --generations 10 --population 50 --seed 42
python cli.py evolve --length 10 --generations 5 --selection roulette --json
```

### 6. Distributed Component Audit
```bash
python cli.py audit --task-id TASK-001 --primary-metric 28.4 --status-descriptor DISCORDANT_ANOMALY
python cli.py audit --task-id TASK-001 --is-critical-flag --json
```

### 7. Supervisory Chat
```bash
python cli.py chat "What is the system status?"
python cli.py chat "Explain specifications" --json
```

### 8. Audit Trail Verification
```bash
python cli.py verify-audit
python cli.py verify-audit --json
```

### Parameter Reference

| Command | Description | Key Parameters |
|:--------|:------------|:---------------|
| `rate` | Calculate mutation rates | `--mncl2`, `--dntp-imbalance`, `--cycles`, `--length` |
| `poisson` | Poisson distribution | `--lambda-val`, `--max-k` |
| `library` | Library size estimation | `--positions`, `--choices`, `--size` |
| `simulate` | Simulate mutations | `--sequence`, `--lambda-val`, `--seed` |
| `evolve` | Directed evolution | `--length`, `--generations`, `--population`, `--selection` |
| `audit` | Component audit | `--task-id`, `--primary-metric`, `--status-descriptor` |
| `chat` | Supervisory chat | `query` (positional) |
| `verify-audit` | Verify audit integrity | `--json` |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Configurable Secret Key:** Set `AUDIT_SECRET_KEY` environment variable for persistent audit integrity (generates ephemeral key if not set).
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances, Claude, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.

### Environment Variables

| Variable | Description | Default |
|:---------|:------------|:--------|
| `AUDIT_SECRET_KEY` | HMAC-SHA256 key for audit trail | Random (ephemeral) |
| `MODEL_PROVIDER` | LLM provider (mock/ollama/claude/openai) | mock |

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py --tasks 1000 --concurrency 8
```

Run the FastAPI server:

```bash
python cli.py serve --host 0.0.0.0 --port 8000
```

---

## 🐳 Container Deployment

```bash
docker build -t directed-evolution-ep-pcr-agent .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=your-secret-key directed-evolution-ep-pcr-agent
```

Or using docker-compose:

```bash
AUDIT_SECRET_KEY=your-secret-key docker-compose up -d
```

---

## 📁 Project Structure

```
directed-evolution-ep-pcr-agent/
├── agents/                    # Distributed component system
│   ├── base.py               # PHI guard, HMAC audit trail
│   ├── models.py             # Pydantic data models
│   ├── workers.py            # Specialized audit workers
│   ├── supervisor.py         # Multi-worker orchestrator
│   ├── llm_factory.py        # LLM provider factory
│   ├── api.py                # FastAPI REST endpoints
│   ├── learning.py           # Bayesian calibration engine
│   ├── metrics.py            # Prometheus metrics
│   └── streamer.py           # WebSocket telemetry
├── directed_evolution/        # Core ep PCR engine
│   ├── engine.py             # Mutation rates, Poisson, NK fitness
│   ├── cli.py                # CLI interface
│   ├── models.py             # Data model exports
│   ├── agents.py             # Domain-specific agents
│   └── server.py             # FastAPI server factory
├── tests/                     # Test suite
├── web/                       # Operations console (HTML)
├── enrichment.py              # Enrichment feature suite
├── simulator.py               # High-throughput simulation
├── cli.py                     # Top-level CLI entry point
├── pyproject.toml             # Project configuration
├── Dockerfile                 # Container build
└── docker-compose.yml         # Container orchestration
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
