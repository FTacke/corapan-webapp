# BlackLab Deployment (Corpus Name + Runtime Config)

## Purpose
This document describes how the CO.RA.PAN backend connects to BlackLab, how the corpus name is configured, and how to verify the deployment.

## Required Environment Variables
- `BLS_BASE_URL` – BlackLab server base URL (must include /blacklab-server).
  - Example: `http://localhost:8081/blacklab-server`
- `BLS_CORPUS` – BlackLab corpus/index name (default: `index`).
  - This must match the corpus ID returned by BlackLab.

### How to discover available corpora
Run:

```
GET ${BLS_BASE_URL}/corpora?outputformat=json
```

Look for corpus IDs in the response (often `corpora[].corpusId`).

## Runtime Validation Behavior
On the first BlackLab request, the app fetches the corpus list and logs a warning if the configured `BLS_CORPUS` is missing. If a request fails because the corpus does not exist, the error message will include the configured corpus name and the list of available corpora.

## Quick Validation Checklist
1. BlackLab is reachable:
   - `GET ${BLS_BASE_URL}/`
2. Corpora list includes the configured corpus:
   - `GET ${BLS_BASE_URL}/corpora?outputformat=json`
3. Hits endpoint works:
   - `GET ${BLS_BASE_URL}/corpora/${BLS_CORPUS}/hits?patt=[lemma="casa"]&number=1&wordsaroundhit=3`

## Notes
- Default corpus is `index` to match production deployments.
- All application calls use `/corpora/${BLS_CORPUS}/...` and must match the BlackLab index name.
