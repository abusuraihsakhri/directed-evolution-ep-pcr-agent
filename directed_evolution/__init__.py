"""
Directed Evolution / Error-Prone PCR: mutation rates, Poisson distribution,
library estimation, fitness landscapes, and selection simulation.
"""
__version__ = "3.0.0"

from .engine import (
    PCRConditions, MutationRateResult, LibraryStats,
    MutationEvent, FitnessResult,
    calculate_mutation_rate,
    poisson_probability, poisson_cumulative, mutation_distribution,
    library_size_for_coverage, coverage_at_library_size, library_diversity,
    shannon_entropy, simpson_diversity,
    simulate_mutations, translate_codon, translate_sequence, classify_mutations,
    nk_fitness, tournament_selection, roulette_selection,
    simulate_directed_evolution, full_ep_pcr_analysis,
)
