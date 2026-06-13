"use client";

import { useState, useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import StatementCard from "@/components/StatementCard";
import { Search, X, Loader2 } from "lucide-react";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [activeQuery, setActiveQuery] = useState("");
  const [offset, setOffset] = useState(0);
  const limit = 10;

  const { data, isLoading, isFetching } = useQuery({
    queryKey: ["search", activeQuery, offset],
    queryFn: () =>
      api.search(activeQuery, {
        limit: String(limit),
        offset: String(offset),
      }),
    enabled: activeQuery.length >= 2,
  });

  const { data: suggestionsData } = useQuery({
    queryKey: ["suggestions", query],
    queryFn: () => api.getSearchSuggestions(query),
    enabled: query.length >= 2 && query !== activeQuery,
  });

  const handleSearch = useCallback(() => {
    if (query.trim().length < 2) return;
    setActiveQuery(query.trim());
    setOffset(0);
  }, [query]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") handleSearch();
  };

  const handleClear = () => {
    setQuery("");
    setActiveQuery("");
    setOffset(0);
  };

  const results = data?.data?.results || [];
  const total = data?.data?.total || 0;
  const suggestions = suggestionsData?.data || [];

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
          Search Statements
        </h1>
        <p className="text-gray-500 dark:text-gray-400">
          Search by minister name, topic, keyword, or portfolio
        </p>
      </div>

      {/* Search box */}
      <div className="relative mb-6">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search
              size={18}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
            />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Search — e.g. 'health hospitals' or 'Satheesan'"
              className="w-full pl-10 pr-10 py-3 border border-gray-300 dark:border-gray-700
                rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100
                placeholder-gray-400 dark:placeholder-gray-500
                focus:outline-none focus:border-green-500 focus:ring-1 focus:ring-green-500 text-sm"
            />
            {query && (
              <button
                onClick={handleClear}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
              >
                <X size={16} />
              </button>
            )}
          </div>
          <button
            onClick={handleSearch}
            disabled={query.length < 2}
            className="bg-green-700 text-white px-6 py-3 rounded-lg font-medium hover:bg-green-800 disabled:opacity-50 transition-colors"
          >
            Search
          </button>
        </div>

        {/* Suggestions */}
        {suggestions.length > 0 && query !== activeQuery && (
          <div className="absolute top-full left-0 right-0 mt-1 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-10 overflow-hidden">
            {suggestions.map((s: Record<string, string>, i: number) => (
              <button
                key={i}
                onClick={() => {
                  setQuery(s.value);
                  setActiveQuery(s.value);
                  setOffset(0);
                }}
                className="w-full text-left px-4 py-2.5 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 flex items-center gap-2"
              >
                <span
                  className={`text-xs px-1.5 py-0.5 rounded ${
                    s.type === "MLA"
                      ? "bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-400"
                      : "bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-400"
                  }`}
                >
                  {s.type}
                </span>
                {s.label}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Example searches */}
      {!activeQuery && (
        <div className="mb-8">
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-3">
            Try searching for:
          </p>
          <div className="flex flex-wrap gap-2">
            {[
              "hospital",
              "school",
              "Satheesan",
              "Pinarayi",
              "infrastructure",
              "budget",
            ].map((example) => (
              <button
                key={example}
                onClick={() => {
                  setQuery(example);
                  setActiveQuery(example);
                }}
                className="text-sm border border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 px-3 py-1.5 rounded-full hover:border-green-400 hover:text-green-700 dark:hover:border-green-600 dark:hover:text-green-400 transition-colors"
              >
                {example}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Results */}
      {activeQuery && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {isFetching ? (
                <span className="flex items-center gap-1.5">
                  <Loader2 size={14} className="animate-spin" />
                  Searching...
                </span>
              ) : (
                <>
                  {total > 0
                    ? `${total} results for "${activeQuery}"`
                    : `No results for "${activeQuery}"`}
                </>
              )}
            </p>
          </div>

          {isLoading ? (
            <div className="space-y-4">
              {[...Array(3)].map((_, i) => (
                <div
                  key={i}
                  className="border border-gray-200 dark:border-gray-700 rounded-lg p-5 animate-pulse"
                >
                  <div className="h-4 bg-gray-200 dark:bg-gray-800 rounded w-32 mb-3" />
                  <div className="h-16 bg-gray-200 dark:bg-gray-800 rounded" />
                </div>
              ))}
            </div>
          ) : results.length === 0 ? (
            <div className="text-center py-16 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-900">
              <Search
                size={40}
                className="text-gray-300 dark:text-gray-600 mx-auto mb-3"
              />
              <p className="text-gray-600 dark:text-gray-400 font-medium">
                No results found
              </p>
              <p className="text-gray-500 dark:text-gray-500 text-sm mt-1">
                Try different keywords or check the spelling
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {results.map((result: Record<string, unknown>) => (
                <StatementCard
                  key={result.id as number}
                  statement={
                    result as unknown as Parameters<
                      typeof StatementCard
                    >[0]["statement"]
                  }
                />
              ))}
            </div>
          )}

          {/* Pagination */}
          {total > limit && (
            <div className="flex items-center justify-between mt-8 pt-4 border-t border-gray-200 dark:border-gray-800">
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Showing {offset + 1}–{Math.min(offset + limit, total)} of{" "}
                {total}
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => setOffset(Math.max(0, offset - limit))}
                  disabled={offset === 0}
                  className="px-3 py-1.5 text-sm border border-gray-200 dark:border-gray-700 rounded-lg disabled:opacity-50 hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300 transition-colors"
                >
                  Previous
                </button>
                <button
                  onClick={() => setOffset(offset + limit)}
                  disabled={offset + limit >= total}
                  className="px-3 py-1.5 text-sm border border-gray-200 dark:border-gray-700 rounded-lg disabled:opacity-50 hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300 transition-colors"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
