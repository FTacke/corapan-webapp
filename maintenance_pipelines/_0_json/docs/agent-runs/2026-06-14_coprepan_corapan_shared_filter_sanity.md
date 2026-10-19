# CO.PRE.PAN/CORAPAN Shared Filter Sanity

| Filter | CO.PRE.PAN count | CORAPAN count | Same filter works |
| --- | ---: | ---: | --- |
| `morph.TenseRole == "finite_verb"` | 414395 | 28506 | True |
| `morph.PastType == "simplePast"` | 420702 | 27658 | True |
| `morph.TenseRole == "aux_passive"` | 20790 | 1495 | True |
| `morph.VoiceType == "passive"` | 46535 | 3412 | True |
| `morph.FutureType == "periphrasticFuture"` | 6918 | 4655 | True |
| `morph.TenseRole == "lexical_participle"` | 28907 | 2198 | True |
| `morph.VerbLemma exists` | 497351 | 36984 | True |

## Hard Failures

None.

## Decision

The same morph filters work without corpus-specific label aliases.
