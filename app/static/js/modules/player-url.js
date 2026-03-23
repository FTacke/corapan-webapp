export function encodePlayerParam(value) {
  return encodeURIComponent(value || "");
}

export function buildPlayerUrl({ transcriptionPath, audioPath, tokenId } = {}) {
  const transcriptionParam = encodePlayerParam(transcriptionPath);
  const audioParam = encodePlayerParam(audioPath);
  let url = `/player?transcription=${transcriptionParam}&audio=${audioParam}`;
  if (tokenId) {
    url += `&token_id=${encodeURIComponent(tokenId)}`;
  }
  return url;
}
