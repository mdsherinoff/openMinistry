export function getPartyFlagUrl(party: string | null | undefined) {
  const slug = getPartySlug(party);

  return slug ? `/party-flags/${slug}.png` : null;
}

export function getPartySlug(party: string | null | undefined) {
  if (!party) {
    return null;
  }

  const slug = party
    .trim()
    .toLowerCase()
    .replace(/&/g, " and ")
    .replace(/\+/g, " plus ")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");

  return slug || null;
}
