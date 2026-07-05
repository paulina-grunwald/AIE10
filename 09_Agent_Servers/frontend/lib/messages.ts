export function getMessageText(content: unknown): string {
  if (typeof content === "string") return content;
  if (Array.isArray(content)) {
    return content
      .map((block) => {
        if (typeof block === "string") return block;
        if (block && typeof block === "object" && "text" in block) {
          return String((block as { text?: unknown }).text ?? "");
        }
        return "";
      })
      .join("");
  }
  return "";
}

export type SearchResult = {
  title: string;
  url: string;
  content: string;
  score?: number;
};

export function parseSearchResults(text: string): SearchResult[] | null {
  const trimmed = text.trim();
  if (!trimmed.startsWith("{") && !trimmed.startsWith("[")) return null;
  try {
    const data = JSON.parse(trimmed);
    const results = Array.isArray(data) ? data : data?.results;
    if (!Array.isArray(results)) return null;
    return results
      .filter((result) => result && typeof result === "object" && "url" in result)
      .map((result) => ({
        title: String(result.title ?? result.url ?? "Untitled"),
        url: String(result.url ?? ""),
        content: String(result.content ?? result.snippet ?? ""),
        score: typeof result.score === "number" ? result.score : undefined,
      }));
  } catch {
    return null;
  }
}

// Split a RAG text result (chunks joined by blank lines) into passages.
export function splitPassages(text: string): string[] {
  return text
    .split(/\n{2,}/)
    .map((passage) => passage.trim())
    .filter(Boolean);
}

// Pull the search query out of a tool call's arguments. Different tools name
// the field differently (query, __arg1), so fall back to the first string.
export function getToolQuery(args: unknown): string | undefined {
  if (!args || typeof args !== "object") return undefined;
  const record = args as Record<string, unknown>;
  const candidate = record.query ?? record.__arg1 ?? record.q;
  if (typeof candidate === "string") return candidate;
  const firstString = Object.values(record).find((v) => typeof v === "string");
  return typeof firstString === "string" ? firstString : undefined;
}

export function hostname(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

export function toolLabel(name?: string): string {
  switch (name) {
    case "retrieve_information":
      return "Knowledge base";
    case "tavily_search":
    case "tavily_search_results_json":
      return "Web search";
    case "arxiv":
      return "Arxiv";
    default:
      return name ?? "tool";
  }
}
