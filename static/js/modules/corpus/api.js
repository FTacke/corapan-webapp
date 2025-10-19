const ENDPOINT = '/corpus/search';

export async function fetchCorpus(queryParams) {
  const url = new URL(ENDPOINT, window.location.origin);
  queryParams.forEach((value, key) => {
    url.searchParams.append(key, value);
  });
  const response = await fetch(url, {
    headers: {
      Accept: 'application/json'
    }
  });
  if (!response.ok) {
    throw new Error('Unable to fetch corpus data');
  }
  return response.json();
}