// Brand-color markers for known fuel retailers, keyed by substring match against
// the station's `brand`/`name` field (as tagged in OSM). There's no reliable way to
// fetch and redistribute actual trademarked logo bitmaps here, so stations are shown
// as colored pins using each network's real brand color + a short abbreviation instead —
// visually distinct on the map without bundling logo assets.
interface BrandStyle {
  color: string;
  abbr: string;
  textColor: string;
}

const BRAND_STYLES: Array<{ match: RegExp; style: BrandStyle }> = [
  { match: /роснефт/i, style: { color: "#FFCC00", abbr: "Р", textColor: "#111111" } },
  { match: /nnk|ннк|независимая нефтяная/i, style: { color: "#0057A8", abbr: "ННК", textColor: "#fff" } },
  { match: /газпром/i, style: { color: "#003D7C", abbr: "ГН", textColor: "#fff" } },
  { match: /лукойл|lukoil/i, style: { color: "#E30613", abbr: "Л", textColor: "#fff" } },
  { match: /shell/i, style: { color: "#ED1C24", abbr: "S", textColor: "#FFD100" } },
  { match: /татнефт/i, style: { color: "#C8102E", abbr: "Т", textColor: "#fff" } },
  { match: /башнефт/i, style: { color: "#004B87", abbr: "Б", textColor: "#fff" } },
  { match: /alliance|альянс/i, style: { color: "#F7941D", abbr: "А", textColor: "#fff" } },
  { match: /нефтьмагистраль/i, style: { color: "#1F8A5B", abbr: "НМ", textColor: "#fff" } },
  { match: /трасса/i, style: { color: "#3A6EA5", abbr: "ТР", textColor: "#fff" } },
  { match: /teboil|тебойл/i, style: { color: "#004F9F", abbr: "TB", textColor: "#fff" } },
];

const DEFAULT_STYLE: BrandStyle = { color: "#5A626B", abbr: "?", textColor: "#fff" };

/** Sentinel key for stations with no brand/network tag, used wherever brands are filtered by key. */
export const NO_BRAND = "__no_brand__";

export function brandStyle(brand: string | null): BrandStyle {
  if (!brand) return DEFAULT_STYLE;
  const found = BRAND_STYLES.find(({ match }) => match.test(brand));
  return found?.style ?? DEFAULT_STYLE;
}
