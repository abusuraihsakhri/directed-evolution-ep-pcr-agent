# Directed Evolution / Error-Prone PCR

Mutation rate calculation, Poisson distribution analysis, library size estimation, mutation simulation, fitness landscape modeling (NK model), and selection pressure simulation.

## Features

- **Mutation Rate Calculation**: Based on MnCl2 concentration, dNTP imbalance, and cycle number
- **Poisson Distribution**: P(k) = e^(-λ) × λ^k / k! for mutation count probabilities
- **Library Estimation**: Coverage = 1 - (1 - 1/N)^L for library sizing
- **Diversity Metrics**: Shannon entropy and Simpson's diversity index
- **Mutation Simulation**: Simulate error-prone PCR on DNA sequences with codon classification
- **Fitness Landscape**: NK model with configurable epistasis (K parameter)
- **Selection Simulation**: Tournament and roulette wheel selection over generations

## Quick Start

```bash
# Calculate mutation rates
python cli.py rate --mncl2 0.5 --cycles 30 --length 1000

# Poisson distribution
python cli.py poisson --lambda-val 3.0

# Library size estimation
python cli.py library --positions 5 --choices 4

# Simulate mutations on DNA
python cli.py simulate --sequence ATGCGATCGATCG --lambda-val 1.0 --seed 42

# Simulate directed evolution
python cli.py evolve --length 20 --generations 10 --population 100 --seed 42
```

## Python API

```python
from directed_evolution import (
    PCRConditions, calculate_mutation_rate,
    poisson_probability, library_size_for_coverage,
    simulate_mutations, simulate_directed_evolution,
)

# Calculate mutation rate
conditions = PCRConditions(mncl2_concentration=0.5, dntp_imbalance=1.0,
                            cycle_number=30, template_length=1000)
rate = calculate_mutation_rate(conditions)
print(f"Expected mutations: {rate.expected_mutations:.2f}")

# Library sizing
lib_size = library_size_for_coverage(num_variants=1000000, coverage=0.95)
print(f"Library size for 95% coverage: {lib_size:,}")

# Simulate mutations
mutated, events = simulate_mutations('ATGCGATCGATCG', lambda_val=2.0, seed=42)
```

## Mutation Rate Model

| Factor | Effect |
|--------|--------|
| MnCl2 | ~3x increase per 0.1 mM above 0.05 mM |
| dNTP imbalance | ~1.5x per 0.5 ratio unit above 1.0 |
| Cycle number | Linear accumulation |
| Taq baseline | ~2×10⁻⁴ errors/bp/cycle |

## License

MIT License.
