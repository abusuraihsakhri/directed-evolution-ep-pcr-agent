"""
CLI module for Directed Evolution / Error-Prone PCR.
"""
import argparse
import json
import sys

from .engine import (
    PCRConditions,
    calculate_mutation_rate,
    poisson_probability, poisson_cumulative, mutation_distribution,
    library_size_for_coverage, coverage_at_library_size, library_diversity,
    simulate_mutations, translate_sequence, classify_mutations,
    simulate_directed_evolution, full_ep_pcr_analysis,
)


def cmd_rate(args):
    """Calculate mutation rates."""
    conditions = PCRConditions(
        mncl2_concentration=args.mncl2,
        dntp_imbalance=args.dntp_imbalance,
        cycle_number=args.cycles,
        template_length=args.length,
    )
    result = calculate_mutation_rate(conditions)
    
    output = {
        'per_bp_per_cycle': result.per_bp_per_cycle,
        'per_bp_total': result.per_bp_total,
        'expected_mutations': result.expected_mutations,
        'mutation_spectrum': result.mutation_spectrum,
    }
    
    if args.json:
        print(json.dumps(output, indent=2))
    else:
        print("Mutation Rate Analysis")
        print("=" * 40)
        print(f"  MnCl2:        {args.mncl2} mM")
        print(f"  dNTP ratio:   {args.dntp_imbalance}")
        print(f"  Cycles:       {args.cycles}")
        print(f"  Template:     {args.length} bp")
        print(f"\n  Per bp per cycle: {result.per_bp_per_cycle:.2e}")
        print(f"  Per bp total:     {result.per_bp_total:.2e}")
        print(f"  Expected mutations (λ): {result.expected_mutations:.2f}")
    
    return 0


def cmd_poisson(args):
    """Calculate Poisson distribution."""
    dist = mutation_distribution(args.lambda_val, args.max_k)
    
    if args.json:
        print(json.dumps(dist, indent=2))
    else:
        print(f"Poisson Distribution (λ = {args.lambda_val})")
        print("=" * 40)
        print(f"{'k':>5} {'P(k)':>12} {'P(≤k)':>12}")
        print("-" * 32)
        cumulative = 0.0
        for k, p in dist.items():
            cumulative += p
            print(f"{k:>5} {p:>12.6f} {cumulative:>12.6f}")
    
    return 0


def cmd_library(args):
    """Estimate library size and diversity."""
    total_variants = library_diversity(args.positions, args.choices)
    lib_95 = library_size_for_coverage(total_variants, 0.95)
    lib_99 = library_size_for_coverage(total_variants, 0.99)
    
    if args.size:
        coverage = coverage_at_library_size(total_variants, args.size)
    else:
        coverage = None
    
    output = {
        'positions': args.positions,
        'choices_per_position': args.choices,
        'total_variants': total_variants,
        'library_size_95': lib_95,
        'library_size_99': lib_99,
    }
    if coverage is not None:
        output['coverage_at_size'] = coverage
    
    if args.json:
        print(json.dumps(output, indent=2))
    else:
        print("Library Diversity Estimation")
        print("=" * 40)
        print(f"  Positions:        {args.positions}")
        print(f"  Choices/position: {args.choices}")
        print(f"  Total variants:   {total_variants:,}")
        print(f"  Library for 95%:  {lib_95:,}")
        print(f"  Library for 99%:  {lib_99:,}")
        if coverage is not None:
            print(f"  Coverage at {args.size:,}: {coverage:.4f}")
    
    return 0


def cmd_simulate(args):
    """Simulate mutations on a DNA sequence."""
    mutated, events = simulate_mutations(args.sequence, args.lambda_val, seed=args.seed)
    
    orig_protein = translate_sequence(args.sequence)
    mut_protein = translate_sequence(mutated)
    
    classified = classify_mutations(args.sequence.upper(), mutated)
    
    output = {
        'original': args.sequence,
        'mutated': mutated,
        'original_protein': orig_protein,
        'mutated_protein': mut_protein,
        'num_mutations': len(events),
        'mutations': [
            {
                'position': e.position,
                'original': e.original_codon,
                'mutated': e.mutated_codon,
                'synonymous': e.is_synonymous,
                'nonsense': e.is_nonsense,
            }
            for e in classified
        ],
    }
    
    if args.json:
        print(json.dumps(output, indent=2))
    else:
        print("Mutation Simulation")
        print("=" * 40)
        print(f"  Original:  {args.sequence}")
        print(f"  Mutated:   {mutated}")
        print(f"  Mutations: {len(events)}")
        print(f"  Protein:   {orig_protein} -> {mut_protein}")
        for e in classified:
            mut_type = 'synonymous' if e.is_synonymous else ('nonsense' if e.is_nonsense else 'missense')
            print(f"    pos {e.position}: {e.original_codon}->{e.mutated_codon} ({e.original_aa}->{e.mutated_aa}, {mut_type})")
    
    return 0


def cmd_evolve(args):
    """Simulate directed evolution."""
    initial = [0] * args.length
    result = simulate_directed_evolution(
        initial_genotype=initial,
        n_generations=args.generations,
        population_size=args.population,
        mutation_rate=args.mutation_rate,
        selection_method=args.selection,
        tournament_size=args.tournament_size,
        k=args.k,
        seed=args.seed,
    )
    
    output = {
        'best_fitness': result['best_fitness'],
        'best_genotype': result['best_genotype'],
        'n_generations': result['n_generations'],
        'fitness_history': result['best_fitness_history'],
    }
    
    if args.json:
        print(json.dumps(output, indent=2))
    else:
        print("Directed Evolution Simulation")
        print("=" * 40)
        print(f"  Generations:  {args.generations}")
        print(f"  Population:   {args.population}")
        print(f"  Mutation rate: {args.mutation_rate}")
        print(f"  Selection:    {args.selection}")
        print(f"\n  Best fitness: {result['best_fitness']:.4f}")
        print(f"  Best genotype: {''.join(map(str, result['best_genotype']))}")
        print(f"\n  Fitness history:")
        for i, f in enumerate(result['best_fitness_history']):
            print(f"    Gen {i+1}: {f:.4f}")
    
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog='directed-evolution-ep-pcr-agent',
        description='Directed Evolution / Error-Prone PCR: mutation rates, library estimation, fitness landscapes',
    )
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    # Rate
    p_rate = subparsers.add_parser('rate', help='Calculate mutation rates')
    p_rate.add_argument('--mncl2', type=float, default=0.5, help='MnCl2 concentration (mM)')
    p_rate.add_argument('--dntp-imbalance', type=float, default=1.0, help='dNTP imbalance ratio')
    p_rate.add_argument('--cycles', type=int, default=30, help='PCR cycles')
    p_rate.add_argument('--length', type=int, default=1000, help='Template length (bp)')
    p_rate.add_argument('--json', action='store_true', help='JSON output')
    
    # Poisson
    p_poisson = subparsers.add_parser('poisson', help='Poisson distribution')
    p_poisson.add_argument('--lambda-val', type=float, required=True, help='Lambda (expected mutations)')
    p_poisson.add_argument('--max-k', type=int, default=20, help='Max k to calculate')
    p_poisson.add_argument('--json', action='store_true', help='JSON output')
    
    # Library
    p_lib = subparsers.add_parser('library', help='Library size estimation')
    p_lib.add_argument('--positions', type=int, required=True, help='Number of random positions')
    p_lib.add_argument('--choices', type=int, default=4, help='Choices per position')
    p_lib.add_argument('--size', type=int, help='Library size for coverage calculation')
    p_lib.add_argument('--json', action='store_true', help='JSON output')
    
    # Simulate
    p_sim = subparsers.add_parser('simulate', help='Simulate mutations')
    p_sim.add_argument('--sequence', required=True, help='DNA sequence')
    p_sim.add_argument('--lambda-val', type=float, required=True, help='Expected mutations')
    p_sim.add_argument('--seed', type=int, help='Random seed')
    p_sim.add_argument('--json', action='store_true', help='JSON output')
    
    # Evolve
    p_evo = subparsers.add_parser('evolve', help='Simulate directed evolution')
    p_evo.add_argument('--length', type=int, default=20, help='Genotype length')
    p_evo.add_argument('--generations', type=int, default=10, help='Number of generations')
    p_evo.add_argument('--population', type=int, default=100, help='Population size')
    p_evo.add_argument('--mutation-rate', type=float, default=0.01, help='Per-site mutation rate')
    p_evo.add_argument('--selection', default='tournament', choices=['tournament', 'roulette'])
    p_evo.add_argument('--tournament-size', type=int, default=3)
    p_evo.add_argument('--k', type=int, default=2, help='NK model epistasis parameter')
    p_evo.add_argument('--seed', type=int, help='Random seed')
    p_evo.add_argument('--json', action='store_true', help='JSON output')
    
    args = parser.parse_args(argv)
    
    commands = {
        'rate': cmd_rate,
        'poisson': cmd_poisson,
        'library': cmd_library,
        'simulate': cmd_simulate,
        'evolve': cmd_evolve,
    }
    
    return commands[args.command](args)


if __name__ == '__main__':
    sys.exit(main())
