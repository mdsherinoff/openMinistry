import ministersData from "@/data/ministers.json";
import statementsData from "@/data/statements.json";

// This is a static demo build: there is no backend anymore. Every "api.*"
// function below reads from the JSON snapshot bundled at build time and
// returns `{ data }`, mirroring the shape axios responses used to have —
// so the page components that were written against the live API need no
// changes.

interface StaticMinister {
  id: number;
  name: string;
  name_malayalam: string | null;
  portfolio: string | null;
  party: string | null;
  constituency: string | null;
  is_active: number;
  start_date: string | null;
  bio: string | null;
  image_url: string | null;
  created_at: string;
}

interface StaticStatement {
  id: number;
  minister_id: number;
  article_id: number | null;
  queue_item_id: number | null;
  statement_text: string;
  statement_summary: string | null;
  topic: string | null;
  confidence_score: number | null;
  context_text: string | null;
  statement_date: string | null;
  status: string;
  created_at: string;
  reviewed_at: string | null;
  minister: {
    id: number;
    name: string;
    portfolio: string | null;
    party: string | null;
    constituency: string | null;
    image_url: string | null;
  };
  source: {
    name: string | null;
    url: string | null;
    title: string | null;
    published_at: string | null;
  };
}

const ministers = ministersData as StaticMinister[];
const statements = statementsData as StaticStatement[];

function ok<T>(data: T) {
  return Promise.resolve({ data });
}

function paginate<T>(items: T[], limit?: number, offset?: number) {
  const start = offset ?? 0;
  const end = limit !== undefined ? start + limit : undefined;
  return items.slice(start, end);
}

export const api = {
  // Statements
  getStatements: (params?: Record<string, string>) => {
    const status = params?.status ?? "approved";
    const ministerId = params?.minister_id ? Number(params.minister_id) : undefined;
    const topic = params?.topic;
    const limit = params?.limit ? Number(params.limit) : 20;
    const offset = params?.offset ? Number(params.offset) : 0;

    let results = statements.filter((s) => s.status === status);
    if (ministerId) results = results.filter((s) => s.minister_id === ministerId);
    if (topic) results = results.filter((s) => s.topic === topic);

    results = [...results].sort((a, b) =>
      (b.statement_date ?? b.created_at).localeCompare(a.statement_date ?? a.created_at),
    );

    const page = paginate(results, limit, offset).map((s) => ({
      id: s.id,
      statement_text: s.statement_text,
      statement_summary: s.statement_summary,
      topic: s.topic,
      confidence_score: s.confidence_score,
      context_text: s.context_text,
      queue_item_id: s.queue_item_id,
      statement_date: s.statement_date,
      status: s.status,
      created_at: s.created_at,
      minister: {
        id: s.minister.id,
        name: s.minister.name,
        portfolio: s.minister.portfolio,
        image_url: s.minister.image_url,
      },
      source: s.source,
    }));

    return ok(page);
  },

  getStatementCount: (params?: Record<string, string>) => {
    const status = params?.status ?? "approved";
    const ministerId = params?.minister_id ? Number(params.minister_id) : undefined;
    const topic = params?.topic;

    let results = statements.filter((s) => s.status === status);
    if (ministerId) results = results.filter((s) => s.minister_id === ministerId);
    if (topic) results = results.filter((s) => s.topic === topic);

    return ok({ count: results.length });
  },

  getTopics: () => {
    const counts = new Map<string, number>();
    for (const s of statements) {
      if (s.status !== "approved" || !s.topic) continue;
      counts.set(s.topic, (counts.get(s.topic) ?? 0) + 1);
    }
    const topics = [...counts.entries()]
      .map(([topic, count]) => ({ topic, count }))
      .sort((a, b) => b.count - a.count);
    return ok(topics);
  },

  getStatementDetail: (id: number) => {
    const stmt = statements.find((s) => s.id === id && s.status === "approved");
    if (!stmt) return Promise.reject(new Error("Statement not found"));

    const buildRelated = (s: StaticStatement) => ({
      id: s.id,
      text: s.statement_text,
      topic: s.topic,
      date: s.statement_date,
      minister: {
        id: s.minister.id,
        name: s.minister.name,
        portfolio: s.minister.portfolio,
        party: s.minister.party,
        constituency: s.minister.constituency,
        image_url: s.minister.image_url,
      },
      source: {
        publication: s.source.name,
        url: s.source.url,
        title: s.source.title,
        published_at: s.source.published_at,
      },
      context_text: null as string | null,
      verified_at: null as string | null,
    });

    let related = statements.filter(
      (s) => s.status === "approved" && s.id !== stmt.id && s.article_id === stmt.article_id && stmt.article_id !== null,
    );
    if (related.length === 0 && stmt.queue_item_id !== null) {
      related = statements.filter(
        (s) => s.status === "approved" && s.id !== stmt.id && s.queue_item_id === stmt.queue_item_id,
      );
    }

    return ok({
      ...buildRelated(stmt),
      context_text: stmt.context_text,
      verified_at: stmt.reviewed_at,
      related_statements: related.slice(0, 10).map(buildRelated),
    });
  },

  // Ministers
  getMinisters: (activeOnly: boolean = true) => {
    let results = ministers;
    if (activeOnly) results = results.filter((m) => m.is_active === 1);
    return ok([...results].sort((a, b) => a.name.localeCompare(b.name)));
  },

  getMinisterStatements: (id: number, params?: Record<string, string>) => {
    const minister = ministers.find((m) => m.id === id);
    if (!minister) return Promise.reject(new Error("Minister not found"));

    const limit = params?.limit ? Number(params.limit) : 20;
    const offset = params?.offset ? Number(params.offset) : 0;

    const all = statements
      .filter((s) => s.minister_id === id && s.status === "approved")
      .sort((a, b) => (b.statement_date ?? "").localeCompare(a.statement_date ?? ""));

    const page = paginate(all, limit, offset).map((s) => ({
      id: s.id,
      statement_text: s.statement_text,
      topic: s.topic,
      confidence_score: s.confidence_score,
      statement_date: s.statement_date,
      status: s.status,
      minister: {
        id: minister.id,
        name: minister.name,
        portfolio: minister.portfolio,
        image_url: minister.image_url,
      },
      source: s.source,
    }));

    return ok({
      minister: {
        id: minister.id,
        name: minister.name,
        name_malayalam: minister.name_malayalam,
        portfolio: minister.portfolio,
        image_url: minister.image_url,
        party: minister.party,
        constituency: minister.constituency,
        bio: minister.bio,
        is_active: minister.is_active,
      },
      total: all.length,
      offset,
      limit,
      statements: page,
    });
  },

  getMinisterStats: (id: number) => {
    const minister = ministers.find((m) => m.id === id);
    if (!minister) return Promise.reject(new Error("Minister not found"));

    const all = statements.filter((s) => s.minister_id === id && s.status === "approved");
    const counts = new Map<string, number>();
    for (const s of all) {
      if (!s.topic) continue;
      counts.set(s.topic, (counts.get(s.topic) ?? 0) + 1);
    }
    const topics = [...counts.entries()]
      .map(([topic, count]) => ({ topic, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 5);

    return ok({ total_statements: all.length, topics });
  },

  // Search
  search: (q: string, params?: Record<string, string>) => {
    type SearchResult = {
      id: number;
      statement_text: string;
      topic: string | null;
      statement_date: string | null;
      minister: { id: number; name: string; portfolio: string | null; image_url: string | null };
      source: { name: string | null; url: string | null; title: string | null };
    };

    const query = q.trim();
    if (query.length < 2) {
      return ok({ total: 0, results: [] as SearchResult[], query: q, offset: 0, limit: 0 });
    }

    const limit = params?.limit ? Number(params.limit) : 20;
    const offset = params?.offset ? Number(params.offset) : 0;
    const needle = query.toLowerCase();

    const matches = statements
      .filter(
        (s) =>
          s.status === "approved" &&
          (s.statement_text.toLowerCase().includes(needle) ||
            s.minister.name.toLowerCase().includes(needle) ||
            (s.topic ?? "").toLowerCase().includes(needle)),
      )
      .sort((a, b) => (b.statement_date ?? "").localeCompare(a.statement_date ?? ""));

    const page = paginate(matches, limit, offset).map((s) => ({
      id: s.id,
      statement_text: s.statement_text,
      topic: s.topic,
      statement_date: s.statement_date,
      minister: {
        id: s.minister.id,
        name: s.minister.name,
        portfolio: s.minister.portfolio,
        image_url: s.minister.image_url,
      },
      source: {
        name: s.source.name,
        url: s.source.url,
        title: s.source.title,
      },
    }));

    return ok({ total: matches.length, query: q, results: page, offset, limit });
  },

  getSearchSuggestions: (q: string) => {
    type Suggestion = { type: string; label: string; value: string };
    const query = q.trim();
    if (query.length < 2) return ok([] as Suggestion[]);
    const needle = query.toLowerCase();

    const suggestions: Suggestion[] = [];

    const ministerMatches = [
      ...new Set(
        ministers
          .filter((m) => m.is_active === 1 && m.name.toLowerCase().includes(needle))
          .map((m) => m.name),
      ),
    ].slice(0, 5);
    for (const name of ministerMatches) {
      suggestions.push({ type: "MLA", label: name, value: name });
    }

    const topicMatches = [
      ...new Set(
        statements
          .filter(
            (s) =>
              s.status === "approved" &&
              s.topic &&
              s.topic.toLowerCase().includes(needle),
          )
          .map((s) => s.topic as string),
      ),
    ].slice(0, 5);
    for (const topic of topicMatches) {
      suggestions.push({ type: "Topic", label: topic, value: topic });
    }

    return ok(suggestions);
  },
};
