# Math Review of `proof_antiderivative_error.tex`

## Executive Summary

ReviseAgent extracted 0 function definitions and 2 math-related claims, plus 1 theorem/proof blueprint(s). It machine-refuted 2 claim(s), machine-verified 0 claim(s), flagged 0 LLM-suspected issue(s), and left 3 claim(s) for human follow-up.

## Blueprint-Lite

### Theorem

- Theorem line: `9`
- Theorem type: `theorem`
- Statement: `We have \[ \int_0^1 x^2 \, dx = \frac{1}{2}. \]`
- Proof line: `16`
- Obligations: `3`
- Extracted obligations:
  1. [assertion] `Clearly, the antiderivative of $x^2$ is $x^2/2$.`
  2. [inference] `Therefore \int_0^1 x^2 \, dx = \frac{1}{2}.`
  3. [inference] `Thus the theorem follows.`


## Machine Refuted Claims

### Incorrect definite integral

- Line: `11`
- Status: `machine-refuted`
- Severity: `critical`
- Snippet: `\[
\int_0^1 x^2 \, dx = \frac{1}{2}.
\]`
- Why: The stated value of the definite integral does not match the symbolic computation.
- Fix: Replace the stated value with `\frac{1}{3}` and show the derivation explicitly.
- Evidence: SymPy computed \frac{1}{3} while the draft states \frac{1}{2}.

### Incorrect definite integral

- Line: `19`
- Status: `machine-refuted`
- Severity: `critical`
- Snippet: `\[
\int_0^1 x^2 \, dx = \frac{1}{2}.
\]`
- Why: The stated value of the definite integral does not match the symbolic computation.
- Fix: Replace the stated value with `\frac{1}{3}` and show the derivation explicitly.
- Evidence: SymPy computed \frac{1}{3} while the draft states \frac{1}{2}.


## Machine Verified Claims

No machine-verified claims.

## LLM-Suspected Proof Issues

No LLM-suspected proof issues.

## Needs Human Check

### Weakly justified proof step

- Line: `16`
- Status: `needs-human-check`
- Severity: `major`
- Snippet: `Clearly, the antiderivative of $x^2$ is $x^2/2$.`
- Why: This proof step uses cue words like 'clearly', 'obvious', or 'therefore' and may be skipping a substantive argument.
- Fix: Expand this step into an explicit derivation or cite the exact prior result being used.
- Evidence: Extracted from theorem on line 9 as proof obligation 1.

### Weakly justified proof step

- Line: `16`
- Status: `needs-human-check`
- Severity: `major`
- Snippet: `Therefore \int_0^1 x^2 \, dx = \frac{1}{2}.`
- Why: This proof step uses cue words like 'clearly', 'obvious', or 'therefore' and may be skipping a substantive argument.
- Fix: Expand this step into an explicit derivation or cite the exact prior result being used.
- Evidence: Extracted from theorem on line 9 as proof obligation 2.

### Weakly justified proof step

- Line: `16`
- Status: `needs-human-check`
- Severity: `major`
- Snippet: `Thus the theorem follows.`
- Why: This proof step uses cue words like 'clearly', 'obvious', or 'therefore' and may be skipping a substantive argument.
- Fix: Expand this step into an explicit derivation or cite the exact prior result being used.
- Evidence: Extracted from theorem on line 9 as proof obligation 3.


## Suggested Revision Order

1. Incorrect definite integral
2. Incorrect definite integral
