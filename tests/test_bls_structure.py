#!/usr/bin/env python3
"""Test BlackLab v5 response structure."""

import os
import httpx

BLS_BASE_URL = os.environ.get("BLS_BASE_URL", "http://localhost:8081/blacklab-server")
BLS_CORPUS = os.environ.get("BLS_CORPUS", "index")

response = httpx.get(
    f"{BLS_BASE_URL}/corpora/{BLS_CORPUS}/hits",
    params={"patt": '[lemma="casa"]', "number": "1", "wordsaroundhit": "3"},
    headers={"Accept": "application/json"},
)

data = response.json()
hit = data["hits"][0]

print("Hit top-level keys:", list(hit.keys()))
print("\nMatch keys:", list(hit["match"].keys()))
print("Match has 'word':", "word" in hit["match"])

if "word" in hit["match"]:
    print("Match word array:", hit["match"]["word"])
else:
    print("No 'word' key found")
    print("\nFirst 5 annotation keys in match:")
    for key in list(hit["match"].keys())[:5]:
        print(f"  {key}: {hit['match'][key]}")
