// Browser-side implementation of the repository's documented heuristic models.
// All calculations and exports are local; no external services are called.
const DNA = "ATGC";
const DEFAULT_RATE = 2e-4;

function positiveFinite(value, name, allowZero = false) {
  if (!Number.isFinite(value) || (allowZero ? value < 0 : value <= 0)) {
    throw new RangeError(`${name} must be a finite ${allowZero ? "nonnegative" : "positive"} number`);
  }
  return value;
}

function integerRange(value, name, min, max) {
  if (!Number.isSafeInteger(value) || value < min || value > max) {
    throw new RangeError(`${name} must be an integer from ${min} to ${max}`);
  }
  return value;
}

export function calculateRate({ mncl2, imbalance, cycles, length, taqRate = DEFAULT_RATE }) {
  positiveFinite(mncl2, "MnCl2", true);
  positiveFinite(imbalance, "dNTP ratio");
  positiveFinite(taqRate, "Taq error rate", true);
  integerRange(cycles, "PCR cycles", 1, 10000);
  integerRange(length, "Template length", 1, 1000000);

  const mncl2Factor = 1 + 3 * Math.max(0, mncl2 - 0.05) / 0.1;
  const dntpFactor = 1 + 0.5 * Math.max(0, imbalance - 1);
  const perBpPerCycle = taqRate * mncl2Factor * dntpFactor;
  const perBpTotal = perBpPerCycle * cycles;
  const expectedMutations = perBpTotal * length;
  if (!Number.isFinite(expectedMutations)) throw new RangeError("Calculation overflow");
  return { perBpPerCycle, perBpTotal, expectedMutations };
}

export function poissonProbability(k, lambda) {
  integerRange(k, "Mutation count", 0, 100000);
  positiveFinite(lambda, "Expected mutations", true);
  if (lambda === 0) return k === 0 ? 1 : 0;
  let logFactorial = 0;
  for (let i = 2; i <= k; i++) logFactorial += Math.log(i);
  return Math.exp(-lambda + k * Math.log(lambda) - logFactorial);
}

export function poissonDistribution(lambda, maxK = 20) {
  integerRange(maxK, "Maximum mutation count", 0, 200);
  positiveFinite(lambda, "Expected mutations", true);
  return Array.from({ length: maxK + 1 }, (_, k) => ({
    k,
    probability: poissonProbability(k, lambda),
  }));
}

export function calculateLibrary({ positions, choices, librarySize, coverage = 0.95 }) {
  integerRange(positions, "Randomized positions", 0, 100);
  integerRange(choices, "Choices per position", 1, 100);
  integerRange(librarySize, "Sampled clones", 0, 1000000000);
  if (!Number.isFinite(coverage) || coverage <= 0 || coverage >= 1) {
    throw new RangeError("Desired coverage must be between 0 and 1");
  }
  const variants = choices ** positions;
  if (!Number.isSafeInteger(variants) || variants > 1e12) {
    throw new RangeError("Variant space exceeds the supported browser calculator range (10¹²)");
  }
  if (variants === 1) {
    return { variants, required95: 1, required99: 1, requiredSelected: 1,
      achievedCoverage: librarySize > 0 ? 1 : 0 };
  }
  const logMiss = Math.log1p(-1 / variants);
  const sizeFor = (fraction) => Math.ceil(Math.log1p(-fraction) / logMiss);
  return {
    variants,
    required95: sizeFor(0.95),
    required99: sizeFor(0.99),
    requiredSelected: sizeFor(coverage),
    achievedCoverage: -Math.expm1(librarySize * logMiss),
  };
}

function mulberry32(seed) {
  let state = seed >>> 0;
  return () => {
    state = (state + 0x6D2B79F5) | 0;
    let t = Math.imul(state ^ (state >>> 15), 1 | state);
    t ^= t + Math.imul(t ^ (t >>> 7), 61 | t);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function simulateSequence(sequence, lambda, seed = null) {
  const clean = sequence.replace(/\s+/g, "").toUpperCase();
  if (!clean || clean.length > 100000 || /[^ACGT]/.test(clean)) {
    throw new RangeError("Use 1–100,000 DNA bases containing only A, C, G, T");
  }
  positiveFinite(lambda, "Expected mutations", true);
  if (seed !== null) integerRange(seed, "Seed", 0, 2147483647);
  const rng = seed === null ? Math.random : mulberry32(seed);
  const probability = -Math.expm1(-lambda / clean.length);
  const mutations = [];
  const mutated = Array.from(clean, (original, index) => {
    if (rng() >= probability) return original;
    const choices = [...DNA].filter(base => base !== original);
    const updated = choices[Math.floor(rng() * choices.length)];
    mutations.push({ position: index + 1, before: original, after: updated });
    return updated;
  }).join("");
  return { original: clean, mutated, mutations, count: mutations.length,
    alterationProbabilityPerSite: probability };
}

function getNumber(id) { return Number(document.getElementById(id).value); }
function getOutput(id) { return document.getElementById(id); }

function showMetrics(id, entries, extra = null) {
  const holder = getOutput(id);
  holder.replaceChildren();
  const dl = document.createElement("dl");
  dl.className = "result-grid";
  for (const [key, value] of entries) {
    const item = document.createElement("div");
    const dt = document.createElement("dt");
    const dd = document.createElement("dd");
    dt.textContent = key;
    dd.textContent = String(value);
    item.append(dt, dd);
    dl.append(item);
  }
  holder.append(dl);
  if (extra) {
    const block = document.createElement("pre");
    block.className = "data-preview";
    block.textContent = extra;
    holder.append(block);
  }
}

function format(value, digits = 5) {
  return Number.isInteger(value) ? value.toLocaleString("en-US") :
    Number(value).toPrecision(digits);
}

let latestExport = null;

function downloadLatest() {
  if (!latestExport) return;
  const blob = new Blob([JSON.stringify(latestExport, null, 2) + "\n"], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "directed-evolution-analysis.json";
  document.body.append(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function successfulResult(kind, result) {
  latestExport = { analysis: kind, result };
  document.getElementById("download").disabled = false;
  document.getElementById("status").textContent = `${kind} completed locally.`;
}

function handle(formId, fn) {
  document.getElementById(formId).addEventListener("submit", (event) => {
    event.preventDefault();
    try {
      fn();
    } catch (error) {
      document.getElementById("status").textContent = error.message;
      document.getElementById("status").classList.add("error");
    }
  });
}

function init() {
  handle("rate-form", () => {
    const result = calculateRate({
      mncl2: getNumber("mncl2"), imbalance: getNumber("imbalance"),
      cycles: getNumber("cycles"), length: getNumber("length"),
    });
    showMetrics("rate-output", [
      ["Errors / bp / cycle", format(result.perBpPerCycle)],
      ["Total errors / bp", format(result.perBpTotal)],
      ["Expected mutations (λ)", format(result.expectedMutations)],
    ], "Poisson mutation count P(k), k = 0…20\n" +
      poissonDistribution(result.expectedMutations)
        .map(row => `${String(row.k).padStart(2)}   ${row.probability.toPrecision(5)}`).join("\n"));
    successfulResult("Mutation-rate analysis", {
      ...result, distribution: poissonDistribution(result.expectedMutations),
    });
    document.getElementById("status").classList.remove("error");
  });

  handle("library-form", () => {
    const inputs = {
      positions: getNumber("positions"), choices: getNumber("choices"),
      librarySize: getNumber("clones"),
    };
    const result = calculateLibrary(inputs);
    showMetrics("library-output", [
      ["Possible variants", format(result.variants)],
      ["Required for 95% mean coverage", format(result.required95)],
      ["Required for 99% mean coverage", format(result.required99)],
      ["Expected variant coverage", (100 * result.achievedCoverage).toFixed(2) + "%"],
    ]);
    successfulResult("Library coverage", { inputs, ...result });
    document.getElementById("status").classList.remove("error");
  });

  handle("sequence-form", () => {
    const seq = document.getElementById("sequence").value;
    const rawSeed = document.getElementById("seed").value.trim();
    const result = simulateSequence(seq, getNumber("sequence-lambda"),
      rawSeed ? Number(rawSeed) : null);
    showMetrics("sequence-output", [
      ["Mutated sites", result.count],
      ["Per-site alteration probability", format(result.alterationProbabilityPerSite)],
    ], "Mutated DNA:\n" + result.mutated + "\n\nChanges (1-based):\n" +
      (result.mutations.map(m => `${m.position}: ${m.before} → ${m.after}`).join("\n") || "None"));
    successfulResult("DNA mutation simulation", result);
    document.getElementById("status").classList.remove("error");
  });
  document.getElementById("download").addEventListener("click", downloadLatest);
}

if (typeof document !== "undefined") init();
