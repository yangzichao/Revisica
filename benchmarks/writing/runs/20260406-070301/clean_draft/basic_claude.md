```json
{
  "findings": [
    {
      "category": "grammar",
      "severity": "minor",
      "title": "Malformed 'convergence of … → 0' phrasing",
      "snippet": "Convergence of $u'(t) \\to 0$ follows from the energy identity and boundedness.",
      "explanation": "\"Convergence of X → 0\" conflates two ways of expressing a limit: \"convergence of X to 0\" and \"X → 0\". The preposition 'of' expects a noun phrase, not a full limit statement.",
      "fix": "That $u'(t) \\to 0$ follows from the energy identity and boundedness."
    }
  ]
}
```
