# CORAPAN vs CO.PRE.PAN Tense Schema Diff (before)

CO.PRE.PAN files: 926
CORAPAN files: 146

## Values

### PastType
- CORAPAN-only: `[]`
- CO.PRE.PAN-only: `['perfectInfinitive']`

### FutureType
- CORAPAN-only: `[]`
- CO.PRE.PAN-only: `[]`

### VoiceType
- CORAPAN-only: `['resultative']`
- CO.PRE.PAN-only: `['resultative_or_state']`

### TenseRole
- CORAPAN-only: `['auxiliary', 'compound_participle', 'finite_past', 'future_infinitive']`
- CO.PRE.PAN-only: `['aux_nonfinite_perfect', 'aux_pass_chain', 'aux_passive', 'copula_or_aux', 'copula_resultative', 'finite_verb', 'nonfinite_perfect']`

## Hard Failures

- CORAPAN TenseRole=finite_past count 28483
- CORAPAN-only TenseRole values: ['auxiliary', 'compound_participle', 'finite_past', 'future_infinitive']
- CORAPAN legacy TenseRole=auxiliary count 13847
