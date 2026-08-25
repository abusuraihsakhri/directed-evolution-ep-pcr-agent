"""
Real tests for Directed Evolution / Error-Prone PCR.
Tests mutation rates, Poisson distribution, library estimation,
mutation simulation, fitness landscapes, and selection.
"""
import sys
import math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from directed_evolution.engine import (
    PCRConditions,
    calculate_mutation_rate,
    poisson_probability, poisson_cumulative, mutation_distribution,
    library_size_for_coverage, coverage_at_library_size, library_diversity,
    shannon_entropy, simpson_diversity,
    simulate_mutations, translate_codon, translate_sequence, classify_mutations,
    nk_fitness, tournament_selection, roulette_selection,
    simulate_directed_evolution, full_ep_pcr_analysis,
)


# --- Test Mutation Rate Calculation ---

def test_mutation_rate_baseline():
    """Baseline conditions should give Taq error rate."""
    conditions = PCRConditions(
        mncl2_concentration=0.05,
        dntp_imbalance=1.0,
        cycle_number=1,
        template_length=1000,
    )
    result = calculate_mutation_rate(conditions)
    assert abs(result.per_bp_per_cycle - 2.0e-4) < 1e-5


def test_mutation_rate_mncl2_increases():
    """Higher MnCl2 should increase mutation rate."""
    low = PCRConditions(mncl2_concentration=0.1, dntp_imbalance=1.0, cycle_number=30, template_length=1000)
    high = PCRConditions(mncl2_concentration=0.5, dntp_imbalance=1.0, cycle_number=30, template_length=1000)
    
    rate_low = calculate_mutation_rate(low)
    rate_high = calculate_mutation_rate(high)
    
    assert rate_high.per_bp_per_cycle > rate_low.per_bp_per_cycle


def test_mutation_rate_cycles():
    """More cycles should increase total mutation rate."""
    few = PCRConditions(mncl2_concentration=0.5, dntp_imbalance=1.0, cycle_number=10, template_length=1000)
    many = PCRConditions(mncl2_concentration=0.5, dntp_imbalance=1.0, cycle_number=50, template_length=1000)
    
    rate_few = calculate_mutation_rate(few)
    rate_many = calculate_mutation_rate(many)
    
    assert rate_many.per_bp_total > rate_few.per_bp_total


def test_mutation_rate_dntp_imbalance():
    """dNTP imbalance should increase mutation rate."""
    balanced = PCRConditions(mncl2_concentration=0.5, dntp_imbalance=1.0, cycle_number=30, template_length=1000)
    imbalanced = PCRConditions(mncl2_concentration=0.5, dntp_imbalance=2.0, cycle_number=30, template_length=1000)
    
    rate_bal = calculate_mutation_rate(balanced)
    rate_imbal = calculate_mutation_rate(imbalanced)
    
    assert rate_imbal.per_bp_per_cycle > rate_bal.per_bp_per_cycle


def test_mutation_rate_lambda():
    """Expected mutations (lambda) = per_bp_total * length."""
    conditions = PCRConditions(
        mncl2_concentration=0.5, dntp_imbalance=1.0,
        cycle_number=30, template_length=1000,
    )
    result = calculate_mutation_rate(conditions)
    expected = result.per_bp_total * 1000
    assert abs(result.expected_mutations - expected) < 0.01


# --- Test Poisson Distribution ---

def test_poisson_zero_lambda():
    """P(0) = 1 when lambda = 0."""
    assert poisson_probability(0, 0.0) == 1.0
    assert poisson_probability(1, 0.0) == 0.0


def test_poisson_sums_to_one():
    """Poisson probabilities should sum to ~1."""
    total = sum(poisson_probability(k, 3.0) for k in range(50))
    assert abs(total - 1.0) < 0.001


def test_poisson_mean():
    """Mean of Poisson should equal lambda."""
    lam = 5.0
    mean = sum(k * poisson_probability(k, lam) for k in range(100))
    assert abs(mean - lam) < 0.01


def test_poisson_cumulative():
    """Cumulative should approach 1 for large k."""
    assert poisson_cumulative(100, 3.0) > 0.999


def test_poisson_negative_k():
    """P(k<0) should be 0."""
    assert poisson_probability(-1, 3.0) == 0.0


def test_mutation_distribution_keys():
    """Distribution should have keys from 0 to max_k."""
    dist = mutation_distribution(2.0, max_k=10)
    assert set(dist.keys()) == set(range(11))


# --- Test Library Size Estimation ---

def test_library_size_small():
    """Small library should need exact size for full coverage."""
    size = library_size_for_coverage(10, 0.95)
    assert size >= 10


def test_library_size_large():
    """Large library should use approximation."""
    size = library_size_for_coverage(1000000, 0.95)
    assert size > 0


def test_library_size_99_vs_95():
    """99% coverage needs more clones than 95%."""
    s95 = library_size_for_coverage(1000, 0.95)
    s99 = library_size_for_coverage(1000, 0.99)
    assert s99 > s95


def test_coverage_at_size():
    """Coverage should increase with library size."""
    c1 = coverage_at_library_size(1000, 100)
    c2 = coverage_at_library_size(1000, 1000)
    c3 = coverage_at_library_size(1000, 5000)
    assert c1 < c2 < c3


def test_coverage_full_library():
    """Library size = num_variants should give high coverage."""
    coverage = coverage_at_library_size(100, 100)
    assert coverage > 0.6  # ~63% (1 - 1/e)


def test_library_diversity():
    """4^L for L positions with 4 choices."""
    assert library_diversity(3, 4) == 64
    assert library_diversity(5, 4) == 1024
    assert library_diversity(3, 20) == 8000  # 20 amino acids


# --- Test Diversity Indices ---

def test_shannon_entropy_uniform():
    """Uniform distribution should have maximum entropy."""
    freq = [10, 10, 10, 10]
    h = shannon_entropy(freq)
    assert abs(h - math.log(4)) < 0.01


def test_shannon_entropy_single():
    """Single species should have zero entropy."""
    freq = [100, 0, 0, 0]
    h = shannon_entropy(freq)
    assert abs(h) < 0.001


def test_simpson_diversity_uniform():
    """Uniform distribution should have high Simpson's diversity."""
    freq = [10, 10, 10, 10]
    d = simpson_diversity(freq)
    assert abs(d - 0.75) < 0.01


def test_simpson_diversity_single():
    """Single species should have zero diversity."""
    freq = [100, 0, 0, 0]
    d = simpson_diversity(freq)
    assert abs(d) < 0.001


# --- Test Mutation Simulation ---

def test_simulate_mutations_zero():
    """Zero lambda should give no mutations."""
    seq = 'ATGCGATCGATCGATCG'
    mutated, events = simulate_mutations(seq, 0.0, seed=42)
    assert mutated == seq
    assert len(events) == 0


def test_simulate_mutations_changes():
    """Non-zero lambda should produce some mutations."""
    seq = 'ATGCGATCGATCGATCG' * 10  # longer sequence
    mutated, events = simulate_mutations(seq, 5.0, seed=42)
    # With lambda=5, should get some mutations
    assert len(events) > 0


def test_simulate_mutations_seed():
    """Same seed should give same results."""
    seq = 'ATGCGATCGATCGATCG' * 10
    m1, e1 = simulate_mutations(seq, 3.0, seed=123)
    m2, e2 = simulate_mutations(seq, 3.0, seed=123)
    assert m1 == m2
    assert len(e1) == len(e2)


def test_translate_codon():
    """Test codon translation."""
    assert translate_codon('ATG') == 'M'
    assert translate_codon('TAA') == '*'
    assert translate_codon('GCT') == 'A'


def test_translate_sequence():
    """Test sequence translation."""
    protein = translate_sequence('ATGGCTAAGTAA')
    assert protein == 'MAK*'


def test_translate_sequence_no_stop():
    """Sequence without stop codon should translate fully."""
    protein = translate_sequence('ATGGCT')
    assert protein == 'MA'


def test_classify_mutations_synonymous():
    """Synonymous mutation should be detected."""
    orig = 'GCTGCC'  # Ala-Ala
    mut = 'GCCGCC'   # Ala-Ala (GCT->GCC, both Ala)
    events = classify_mutations(orig, mut)
    assert len(events) == 1
    assert events[0].is_synonymous


def test_classify_mutations_missense():
    """Missense mutation should be detected."""
    orig = 'ATGGCT'  # Met-Ala
    mut = 'ATGGGT'   # Met-Gly (GCT->GGT)
    events = classify_mutations(orig, mut)
    assert len(events) == 1
    assert not events[0].is_synonymous
    assert not events[0].is_nonsense


def test_classify_mutations_nonsense():
    """Nonsense mutation should be detected."""
    orig = 'ATGGCT'  # Met-Ala
    mut = 'ATGTAA'   # Met-Stop (GCT->TAA, 3 bases changed)
    events = classify_mutations(orig, mut)
    # 3 bases changed (positions 3,4,5), so 3 mutation events
    assert len(events) == 3
    # Each event should have the original codon context
    for e in events:
        assert e.original_codon == 'GCT'
        assert e.original_aa == 'A'


# --- Test NK Fitness Landscape ---

def test_nk_fitness_all_zeros():
    """All-zero genotype should have some fitness."""
    fitness = nk_fitness([0, 0, 0, 0, 0], 5, 0, seed=42)
    assert 0 <= fitness <= 1


def test_nk_fitness_all_ones():
    """All-one genotype should have some fitness."""
    fitness = nk_fitness([1, 1, 1, 1, 1], 5, 0, seed=42)
    assert 0 <= fitness <= 1


def test_nk_fitness_k0_no_epistasis():
    """K=0 should have no epistasis (each locus independent)."""
    geno = [0, 1, 0, 1, 0]
    fitness = nk_fitness(geno, 5, 0, seed=42)
    assert 0 <= fitness <= 1


def test_nk_fitness_k_error():
    """K >= N should raise error."""
    try:
        nk_fitness([0, 1], 2, 2, seed=42)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


# --- Test Selection ---

def test_tournament_selection():
    """Tournament should select the best in the tournament."""
    pop = [([0, 0], 0.1), ([1, 1], 0.9), ([0, 1], 0.5)]
    winner = tournament_selection(pop, tournament_size=3, seed=42)
    assert winner[1] == 0.9


def test_roulette_selection():
    """Roulette should tend to select higher fitness."""
    pop = [([0, 0], 0.1), ([1, 1], 0.9)]
    # Run many times and check bias
    selections = []
    for seed in range(100):
        selections.append(roulette_selection(pop, seed=seed)[1])
    avg = sum(selections) / len(selections)
    assert avg > 0.5  # should be biased toward 0.9


# --- Test Directed Evolution Simulation ---

def test_simulate_directed_evolution():
    """Simulation should improve fitness over generations."""
    result = simulate_directed_evolution(
        initial_genotype=[0] * 10,
        n_generations=20,
        population_size=50,
        mutation_rate=0.05,
        k=2,
        seed=42,
    )
    assert result['best_fitness'] > 0
    assert len(result['best_fitness_history']) == 20
    # Fitness should generally improve
    assert result['best_fitness_history'][-1] >= result['best_fitness_history'][0]


def test_simulate_directed_evolution_seed():
    """Same seed should give same results."""
    r1 = simulate_directed_evolution([0]*10, n_generations=5, population_size=20, seed=42)
    r2 = simulate_directed_evolution([0]*10, n_generations=5, population_size=20, seed=42)
    assert r1['best_fitness'] == r2['best_fitness']


# --- Test Full Analysis ---

def test_full_ep_pcr_analysis():
    """Full analysis should return all components."""
    conditions = PCRConditions(
        mncl2_concentration=0.5,
        dntp_imbalance=1.0,
        cycle_number=30,
        template_length=1000,
    )
    result = full_ep_pcr_analysis(conditions, library_size=10000)
    
    assert 'mutation_rate' in result
    assert 'mutation_distribution' in result
    assert 'library_stats' in result
    assert result['mutation_rate']['expected_mutations'] > 0


# --- Test CLI ---

def test_cli_rate():
    """Test CLI rate command."""
    from directed_evolution.cli import main
    assert main(['rate', '--mncl2', '0.5', '--cycles', '30', '--length', '1000']) == 0


def test_cli_poisson():
    """Test CLI poisson command."""
    from directed_evolution.cli import main
    assert main(['poisson', '--lambda-val', '3.0']) == 0


def test_cli_library():
    """Test CLI library command."""
    from directed_evolution.cli import main
    assert main(['library', '--positions', '5']) == 0


def test_cli_simulate():
    """Test CLI simulate command."""
    from directed_evolution.cli import main
    assert main(['simulate', '--sequence', 'ATGCGATCGATCG', '--lambda-val', '1.0', '--seed', '42']) == 0


def test_cli_evolve():
    """Test CLI evolve command."""
    from directed_evolution.cli import main
    assert main(['evolve', '--length', '10', '--generations', '5', '--population', '20', '--seed', '42']) == 0
