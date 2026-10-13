"""
Directed Evolution / Error-Prone PCR Engine
Mutation rate calculation, Poisson distribution, library size estimation,
diversity calculation, selection pressure simulation, and fitness landscape modeling.
"""
import math
import random
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field


# --- Constants ---
# Standard genetic code: codon -> amino acid
GENETIC_CODE = {
    'TTT': 'F', 'TTC': 'F', 'TTA': 'L', 'TTG': 'L',
    'CTT': 'L', 'CTC': 'L', 'CTA': 'L', 'CTG': 'L',
    'ATT': 'I', 'ATC': 'I', 'ATA': 'I', 'ATG': 'M',
    'GTT': 'V', 'GTC': 'V', 'GTA': 'V', 'GTG': 'V',
    'TCT': 'S', 'TCC': 'S', 'TCA': 'S', 'TCG': 'S',
    'CCT': 'P', 'CCC': 'P', 'CCA': 'P', 'CCG': 'P',
    'ACT': 'T', 'ACC': 'T', 'ACA': 'T', 'ACG': 'T',
    'GCT': 'A', 'GCC': 'A', 'GCA': 'A', 'GCG': 'A',
    'TAT': 'Y', 'TAC': 'Y', 'TAA': '*', 'TAG': '*',
    'CAT': 'H', 'CAC': 'H', 'CAA': 'Q', 'CAG': 'Q',
    'AAT': 'N', 'AAC': 'N', 'AAA': 'K', 'AAG': 'K',
    'GAT': 'D', 'GAC': 'D', 'GAA': 'E', 'GAG': 'E',
    'TGT': 'C', 'TGC': 'C', 'TGA': '*', 'TGG': 'W',
    'CGT': 'R', 'CGC': 'R', 'CGA': 'R', 'CGG': 'R',
    'AGT': 'S', 'AGC': 'S', 'AGA': 'R', 'AGG': 'R',
    'GGT': 'G', 'GGC': 'G', 'GGA': 'G', 'GGG': 'G',
}

NUCLEOTIDES = ['A', 'T', 'G', 'C']


# --- Data Models ---

@dataclass
class PCRConditions:
    """Error-prone PCR reaction conditions."""
    mncl2_concentration: float  # mM (typical: 0.1-0.5 mM)
    dntp_imbalance: float       # ratio (1.0 = balanced, >1 = imbalanced)
    cycle_number: int           # PCR cycles
    template_length: int        # bp
    taq_error_rate: float = 2.0e-4  # errors per bp per cycle (Taq baseline)


@dataclass
class MutationRateResult:
    """Calculated mutation rate parameters."""
    per_bp_per_cycle: float     # mutation rate per bp per cycle
    per_bp_total: float         # total mutation rate per bp over all cycles
    expected_mutations: float   # lambda (expected mutations per sequence)
    mutation_spectrum: Dict[str, float]  # transition/transversion ratios


@dataclass
class LibraryStats:
    """Library diversity statistics."""
    expected_unique_variants: int
    library_size_needed: int    # for 95% coverage
    library_size_needed_99: int  # for 99% coverage
    coverage_at_size: float     # coverage at given library size
    num_possible_variants: int
    diversity_index: float      # Shannon entropy


@dataclass
class MutationEvent:
    """A single mutation event."""
    position: int
    original_codon: str
    mutated_codon: str
    original_aa: str
    mutated_aa: str
    is_synonymous: bool
    is_nonsense: bool


@dataclass
class FitnessResult:
    """Result of fitness evaluation."""
    fitness: float
    num_mutations: int
    num_synonymous: int
    num_nonsynonymous: int
    num_nonsense: int


# --- Mutation Rate Calculation ---

def calculate_mutation_rate(conditions: PCRConditions) -> MutationRateResult:
    """Calculate mutation rate based on PCR conditions.
    
    Error rate increases with:
    - MnCl2 concentration (Mn²⁺ reduces Taq fidelity)
    - dNTP imbalance (unequal concentrations cause misincorporation)
    - Cycle number (more cycles = more errors accumulated)
    
    Base error rate: ~2×10⁻⁴ errors/bp/cycle (Taq polymerase)
    MnCl2 effect: ~3x increase per 0.1 mM above 0.05 mM
    dNTP imbalance: ~1.5x increase per 0.5 ratio unit above 1.0
    """
    if (not all(math.isfinite(value) for value in (
        conditions.mncl2_concentration, conditions.dntp_imbalance,
        conditions.taq_error_rate,
    )) or conditions.mncl2_concentration < 0
            or conditions.dntp_imbalance <= 0
            or conditions.taq_error_rate < 0
            or conditions.cycle_number <= 0
            or conditions.template_length <= 0):
        raise ValueError("PCR conditions require finite nonnegative rates, positive cycles, length and dNTP ratio")
    base_rate = conditions.taq_error_rate
    
    # MnCl2 effect (empirical model)
    # At 0.1 mM: ~1x, at 0.5 mM: ~5x increase
    mncl2_factor = 1.0 + 3.0 * max(0, conditions.mncl2_concentration - 0.05) / 0.1
    
    # dNTP imbalance effect
    dntp_factor = 1.0 + 0.5 * max(0, conditions.dntp_imbalance - 1.0)
    
    per_bp_per_cycle = base_rate * mncl2_factor * dntp_factor
    
    # Total per-bp rate over all cycles
    # Each molecule is copied (cycles-1) times on average
    per_bp_total = per_bp_per_cycle * conditions.cycle_number
    
    # Expected mutations per sequence (lambda for Poisson)
    lambda_mut = per_bp_total * conditions.template_length
    
    # Mutation spectrum (simplified)
    # Transitions (A<->G, C<->T) are ~2x more common than transversions
    transition_rate = per_bp_per_cycle * 0.67
    transversion_rate = per_bp_per_cycle * 0.33
    
    return MutationRateResult(
        per_bp_per_cycle=per_bp_per_cycle,
        per_bp_total=per_bp_total,
        expected_mutations=lambda_mut,
        mutation_spectrum={
            'transition_rate': transition_rate,
            'transversion_rate': transversion_rate,
            'transition_ratio': 0.67,
        },
    )


# --- Poisson Distribution ---

def poisson_probability(k: int, lambda_val: float) -> float:
    """Poisson probability mass function: P(k) = e^(-λ) × λ^k / k!
    
    Args:
        k: Number of events
        lambda_val: Expected number of events
    Returns:
        Probability of exactly k events
    """
    if not math.isfinite(lambda_val) or lambda_val < 0:
        raise ValueError("Lambda must be finite and non-negative")
    if k < 0:
        return 0.0
    if lambda_val == 0:
        return 1.0 if k == 0 else 0.0
    
    # Use log to avoid overflow
    log_p = -lambda_val + k * math.log(lambda_val) - math.lgamma(k + 1)
    return math.exp(log_p)


def poisson_cumulative(k: int, lambda_val: float) -> float:
    """Cumulative Poisson distribution: P(X ≤ k)."""
    if not math.isfinite(lambda_val) or lambda_val < 0:
        raise ValueError("Lambda must be finite and non-negative")
    return min(1.0, sum(poisson_probability(i, lambda_val) for i in range(k + 1)))


def mutation_distribution(lambda_val: float, max_k: int = 20) -> Dict[int, float]:
    """Calculate probability distribution of number of mutations.
    
    Args:
        lambda_val: Expected number of mutations
        max_k: Maximum number of mutations to calculate
    Returns:
        Dict mapping number of mutations to probability
    """
    if max_k < 0:
        raise ValueError("max_k must be non-negative")
    if not math.isfinite(lambda_val) or lambda_val < 0:
        raise ValueError("Lambda must be finite and non-negative")
    return {k: poisson_probability(k, lambda_val) for k in range(max_k + 1)}


# --- Library Size Estimation ---

def library_size_for_coverage(num_variants: int, coverage: float = 0.95) -> int:
    """Calculate library size needed to achieve desired coverage.
    
    Coverage = 1 - (1 - 1/N)^L where N = variants, L = library size
    Solving: L = ln(1 - coverage) / ln(1 - 1/N)
    
    Args:
        num_variants: Total number of possible unique variants
        coverage: Desired coverage (0 to 1)
    Returns:
        Required library size
    """
    if num_variants <= 0:
        return 0
    if not math.isfinite(coverage) or coverage <= 0 or coverage >= 1:
        raise ValueError("Coverage must be between 0 and 1 exclusive")
    if num_variants == 1:
        return 1
    
    # For large N, use approximation: L ≈ -N × ln(1 - coverage)
    if num_variants > 1000:
        return int(math.ceil(-num_variants * math.log(1 - coverage)))
    
    return int(math.ceil(
        math.log(1 - coverage) / math.log(1 - 1.0 / num_variants)
    ))


def coverage_at_library_size(num_variants: int, library_size: int) -> float:
    """Calculate coverage achieved with given library size.
    
    Coverage = 1 - (1 - 1/N)^L
    """
    if num_variants <= 0:
        return 1.0
    if library_size <= 0:
        return 0.0
    return -math.expm1(library_size * math.log1p(-1.0 / num_variants)) if num_variants > 1 else 1.0


def library_diversity(num_positions: int, num_choices: int = 4) -> int:
    """Calculate total number of possible variants.
    
    For L random positions with N choices each: N^L variants.
    """
    if num_positions < 0 or num_choices < 1:
        raise ValueError("Positions must be non-negative and choices must be at least one")
    return num_choices ** num_positions


# --- Diversity Calculation ---

def shannon_entropy(frequencies: List[float]) -> float:
    """Calculate Shannon entropy from frequency distribution.
    H = -Σ p_i × ln(p_i)
    """
    entropy = 0.0
    total = sum(frequencies)
    if total == 0:
        return 0.0
    for f in frequencies:
        if f > 0:
            p = f / total
            entropy -= p * math.log(p)
    return entropy


def simpson_diversity(frequencies: List[float]) -> float:
    """Calculate Simpson's diversity index: D = 1 - Σ(p_i²)
    Higher values indicate greater diversity.
    """
    total = sum(frequencies)
    if total == 0:
        return 0.0
    sum_sq = sum((f / total) ** 2 for f in frequencies)
    return 1.0 - sum_sq


# --- Mutation Simulation ---

def simulate_mutations(sequence: str, lambda_val: float,
                        seed: Optional[int] = None) -> Tuple[str, List[MutationEvent]]:
    """Simulate independent nucleotide substitutions without repeated-site hits.

    Sites follow a Poisson process with mean lambda_val / sequence_length.
    The alteration probability is 1 - exp(-lambda_val / sequence_length).
    The bounded site model avoids repeated-hit artifacts and underflow.
    """
    if not sequence or any(base not in "ACGT" for base in sequence.upper()):
        raise ValueError("Sequence must be non-empty DNA (A, C, G, T)")
    if not math.isfinite(lambda_val) or lambda_val < 0:
        raise ValueError("Lambda must be finite and non-negative")

    rng = random.Random(seed)
    original = sequence.upper()
    seq = list(original)
    site_probability = -math.expm1(-lambda_val / len(seq))
    for pos, base in enumerate(seq):
        if rng.random() < site_probability:
            seq[pos] = rng.choice([candidate for candidate in NUCLEOTIDES
                                   if candidate != base])

    mutated = "".join(seq)
    classified = {event.position: event for event in classify_mutations(original, mutated)}
    events = []
    for pos, (before, after) in enumerate(zip(original, mutated)):
        if before != after:
            event = classified.get(pos)
            if event is None:  # Trailing nucleotides beyond a complete codon.
                event = MutationEvent(pos, before, after, "", "", False, False)
            events.append(event)
    return mutated, events


def _poisson_sample(lambda_val: float) -> int:
    """Sample from Poisson distribution using Knuth's algorithm."""
    if lambda_val <= 0:
        return 0
    
    L = math.exp(-lambda_val)
    k = 0
    p = 1.0
    
    while True:
        k += 1
        p *= random.random()
        if p < L:
            break
    
    return k - 1


def translate_codon(codon: str) -> str:
    """Translate a DNA codon to amino acid."""
    return GENETIC_CODE.get(codon.upper(), 'X')


def translate_sequence(dna: str) -> str:
    """Translate a DNA sequence to protein."""
    protein = []
    for i in range(0, len(dna) - 2, 3):
        codon = dna[i:i+3]
        aa = translate_codon(codon)
        protein.append(aa)
        if aa == '*':
            break
    return ''.join(protein)


def classify_mutations(original: str, mutated: str) -> List[MutationEvent]:
    """Classify mutations between original and mutated DNA sequences.
    
    Returns list of mutation events with synonymous/nonsense classification.
    """
    events = []
    for i in range(min(len(original), len(mutated))):
        if original[i] != mutated[i]:
            # Find codon position
            codon_start = (i // 3) * 3
            if codon_start + 3 <= len(original) and codon_start + 3 <= len(mutated):
                orig_codon = original[codon_start:codon_start+3]
                mut_codon = mutated[codon_start:codon_start+3]
                
                orig_aa = translate_codon(orig_codon)
                mut_aa = translate_codon(mut_codon)
                
                events.append(MutationEvent(
                    position=i,
                    original_codon=orig_codon,
                    mutated_codon=mut_codon,
                    original_aa=orig_aa,
                    mutated_aa=mut_aa,
                    is_synonymous=(orig_aa == mut_aa),
                    is_nonsense=(mut_aa == '*'),
                ))
    
    return events


# --- Fitness Landscape (NK Model) ---

def nk_fitness(genotype: List[int], n: int, k: int,
                interactions: Optional[List[List[int]]] = None,
                fitness_table: Optional[Dict] = None,
                seed: Optional[int] = None) -> float:
    """Calculate fitness using the NK fitness landscape model.
    
    N: number of loci
    K: number of epistatic interactions per locus (0 = no epistasis)
    
    Each locus contributes a fitness component based on its own state
    and the states of K neighboring loci.
    
    Args:
        genotype: List of 0s and 1s (binary genotype)
        n: Number of loci
        k: Number of interactions per locus
        interactions: Pre-computed interaction sets (optional)
        fitness_table: Pre-computed fitness contributions (optional)
        seed: Random seed
    Returns:
        Fitness value (0 to 1)
    """
    if seed is not None:
        random.seed(seed)
    
    if len(genotype) != n:
        raise ValueError(f"Genotype length {len(genotype)} != N {n}")
    if n <= 0 or not 0 <= k < n:
        raise ValueError("N must be positive and K must satisfy 0 <= K < N")
    if any(bit not in (0, 1) for bit in genotype):
        raise ValueError("NK genotypes must contain only 0 and 1")
    
    # Generate interaction sets if not provided
    if interactions is None:
        interactions = []
        for i in range(n):
            # K nearest neighbors (circular)
            neighbors = [(i + j + 1) % n for j in range(k)]
            interactions.append(neighbors)
    
    # Generate fitness table if not provided
    if fitness_table is None:
        fitness_table = {}
        for i in range(n):
            num_states = 2 ** (k + 1)  # 2^(K+1) possible states
            for state in range(num_states):
                fitness_table[(i, state)] = random.random()
    
    # Calculate total fitness
    total_fitness = 0.0
    for i in range(n):
        # Build state from locus i and its K interactions
        state_bits = [genotype[i]]
        for neighbor in interactions[i]:
            state_bits.append(genotype[neighbor])
        
        # Convert to integer
        state = 0
        for bit in state_bits:
            state = (state << 1) | bit
        
        total_fitness += fitness_table.get((i, state), 0.5)
    
    return total_fitness / n


def neutral_fitness(genotype: List[int], n: int, k: int = 0) -> float:
    """Simple fitness function: fraction of 1s in genotype (for testing)."""
    return sum(genotype) / n if n > 0 else 0.0


# --- Selection Pressure Simulation ---

def tournament_selection(population: List[Tuple[List[int], float]],
                          tournament_size: int = 3,
                          seed: Optional[int] = None) -> Tuple[List[int], float]:
    """Tournament selection: pick tournament_size individuals, return the best."""
    if seed is not None:
        random.seed(seed)
    
    if not population or tournament_size < 1:
        raise ValueError("Tournament needs a nonempty population and positive size")
    competitors = random.sample(population, min(tournament_size, len(population)))
    return max(competitors, key=lambda x: x[1])


def roulette_selection(population: List[Tuple[List[int], float]],
                        seed: Optional[int] = None) -> Tuple[List[int], float]:
    """Roulette wheel selection proportional to fitness."""
    if seed is not None:
        random.seed(seed)
    
    if not population or any(not math.isfinite(f) or f < 0 for _, f in population):
        raise ValueError("Roulette selection requires finite nonnegative fitness values")
    total_fitness = sum(f for _, f in population)
    if total_fitness == 0:
        return random.choice(population)
    
    pick = random.random() * total_fitness
    current = 0.0
    for genotype, fitness in population:
        current += fitness
        if current >= pick:
            return genotype, fitness
    
    return population[-1]


def simulate_directed_evolution(
    initial_genotype: List[int],
    n_generations: int = 10,
    population_size: int = 100,
    mutation_rate: float = 0.01,
    selection_method: str = 'tournament',
    tournament_size: int = 3,
    n: Optional[int] = None,
    k: int = 2,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """Simulate directed evolution over multiple generations.
    
    Args:
        initial_genotype: Starting genotype
        n_generations: Number of generations
        population_size: Population size per generation
        mutation_rate: Per-site mutation rate
        selection_method: 'tournament' or 'roulette'
        tournament_size: Size for tournament selection
        n: Number of loci (defaults to len(initial_genotype))
        k: Epistasis parameter for NK model
        seed: Random seed
    Returns:
        Dict with evolution statistics
    """
    if seed is not None:
        random.seed(seed)
    
    if n is None:
        n = len(initial_genotype)
    if (n <= 0 or len(initial_genotype) != n or not 0 <= k < n
            or any(bit not in (0, 1) for bit in initial_genotype)
            or n_generations < 1 or population_size < 1
            or not math.isfinite(mutation_rate) or not 0 <= mutation_rate <= 1
            or selection_method not in ("tournament", "roulette")
            or tournament_size < 1):
        raise ValueError("Invalid evolution parameters or binary initial genotype")

    # Initialize fitness table for consistent landscape
    fitness_table = {}
    rng_state = random.getstate()
    for i in range(n):
        num_states = 2 ** (k + 1)
        for state in range(num_states):
            fitness_table[(i, state)] = random.random()
    random.setstate(rng_state)
    
    # Initialize population
    population = [(list(initial_genotype), 0.0) for _ in range(population_size)]
    for i in range(population_size):
        fitness = nk_fitness(population[i][0], n, k, fitness_table=fitness_table)
        population[i] = (population[i][0], fitness)
    
    best_fitness_history = []
    avg_fitness_history = []
    best_genotype = initial_genotype
    best_fitness = 0.0
    
    for gen in range(n_generations):
        # Selection
        new_population = []
        for _ in range(population_size):
            if selection_method == 'tournament':
                parent = tournament_selection(population, tournament_size)
            else:
                parent = roulette_selection(population)
            new_population.append((list(parent[0]), 0.0))
        
        # Mutation
        for i in range(population_size):
            genotype = list(new_population[i][0])
            for j in range(n):
                if random.random() < mutation_rate:
                    genotype[j] = 1 - genotype[j]  # flip bit
            fitness = nk_fitness(genotype, n, k, fitness_table=fitness_table)
            new_population[i] = (genotype, fitness)
        
        population = new_population
        
        # Statistics
        fitnesses = [f for _, f in population]
        best_gen = max(population, key=lambda x: x[1])
        avg_fitness = sum(fitnesses) / len(fitnesses)
        
        best_fitness_history.append(best_gen[1])
        avg_fitness_history.append(avg_fitness)
        
        if best_gen[1] > best_fitness:
            best_fitness = best_gen[1]
            best_genotype = best_gen[0]
    
    return {
        'best_genotype': best_genotype,
        'best_fitness': best_fitness,
        'best_fitness_history': best_fitness_history,
        'avg_fitness_history': avg_fitness_history,
        'n_generations': n_generations,
        'population_size': population_size,
    }


# --- Full Analysis ---

def full_ep_pcr_analysis(conditions: PCRConditions,
                          library_size: int = 10000) -> Dict[str, Any]:
    """Run complete error-prone PCR analysis.
    
    1. Calculate mutation rates
    2. Calculate Poisson distribution
    3. Estimate library statistics
    """
    rate = calculate_mutation_rate(conditions)
    
    dist = mutation_distribution(rate.expected_mutations)
    
    # Library statistics
    # For single mutations: 3 × L possible variants (3 substitutions per position)
    single_variants = 3 * conditions.template_length
    # For up to 3 mutations: approximate
    total_variants = sum(
        math.comb(conditions.template_length, k) * 3**k
        for k in range(min(4, conditions.template_length + 1))
    )
    
    lib_95 = library_size_for_coverage(total_variants, 0.95)
    lib_99 = library_size_for_coverage(total_variants, 0.99)
    coverage = coverage_at_library_size(total_variants, library_size)
    
    return {
        'mutation_rate': {
            'per_bp_per_cycle': rate.per_bp_per_cycle,
            'per_bp_total': rate.per_bp_total,
            'expected_mutations': rate.expected_mutations,
        },
        'mutation_distribution': dist,
        'library_stats': {
            'total_possible_variants': total_variants,
            'library_size_95': lib_95,
            'library_size_99': lib_99,
            'coverage_at_size': coverage,
        },
    }
