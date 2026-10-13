import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { calculateRate, calculateLibrary, poissonDistribution,
  poissonProbability, simulateSequence } from '../web/app.mjs';

test('rate parameters agree with the Python heuristic at baseline', () => {
  const result = calculateRate({ mncl2: 0.05, imbalance: 1, cycles: 1, length: 1000 });
  assert.ok(Math.abs(result.perBpPerCycle - 2e-4) < 1e-12);
  assert.ok(Math.abs(result.expectedMutations - 0.2) < 1e-12);
});

test('Poisson distribution is normalized for moderate lambda', () => {
  const total = poissonDistribution(3, 50).reduce((sum, row) => sum + row.probability, 0);
  assert.ok(Math.abs(total - 1) < 1e-10);
  assert.equal(poissonProbability(0, 0), 1);
  assert.throws(() => poissonProbability(0, NaN), RangeError);
});

test('library coverage has consistent edge case and monotonicity', () => {
  const single = calculateLibrary({ positions: 0, choices: 4, librarySize: 1 });
  assert.equal(single.variants, 1);
  assert.equal(single.required95, 1);
  const smaller = calculateLibrary({ positions: 2, choices: 10, librarySize: 100 });
  const larger = calculateLibrary({ positions: 2, choices: 10, librarySize: 1000 });
  assert.ok(smaller.achievedCoverage < larger.achievedCoverage);
  assert.ok(Math.abs(smaller.achievedCoverage - (1 - (1 - 1 / 100) ** 100)) < 1e-10);
  assert.throws(() => calculateLibrary({ positions: 20, choices: 20, librarySize: 100 }), RangeError);
});

test('mutation simulation preserves length and is seeded', () => {
  const a = simulateSequence('ATGCGATCGATC', 4, 42);
  const b = simulateSequence('ATGCGATCGATC', 4, 42);
  assert.deepEqual(a, b);
  assert.equal(a.original.length, a.mutated.length);
  assert.ok(a.count <= a.original.length);
  assert.equal(simulateSequence('ATG', 0, 42).mutated, 'ATG');
  assert.throws(() => simulateSequence('ATGN', 1), RangeError);
});

test('entry page loads local JavaScript without external runtime dependencies', () => {
  const html = readFileSync(new URL('../web/index.html', import.meta.url), 'utf8');
  assert.match(html, /type="module" src="\.\/app\.mjs"/);
  assert.doesNotMatch(html, /fetch\s*\(/);
  assert.doesNotMatch(html, /HMAC_SHA256_e83|Tasks Processed/);
});
