# Math Review of `wrong_integral.tex`

## Executive Summary

ReviseAgent extracted 0 function definitions and 1 math-related claims, plus 0 theorem/proof blueprint(s). It machine-refuted 1 claim(s), machine-verified 0 claim(s), flagged 0 LLM-suspected issue(s), and left 0 claim(s) for human follow-up.

## Blueprint-Lite

No theorem/proof environments were extracted.

## Machine Refuted Claims

### Incorrect definite integral

- Line: `7`
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

No unresolved math claims.

## Suggested Revision Order

1. Incorrect definite integral
