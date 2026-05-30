"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import StatementCard from "@/components/StatementCard";
import { FileText, ChevronLeft, ChevronRight } from "lucide-react";

export default function StatementsPage() {
  const [offset, setOffset] = useState(0);
  const limit = 10;
  const [selectedTopic, setSelectedTopic] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["statements", offset, selectedTopic],
    queryFn: () =>
      api.getStatements({
        status: "approved",
        limit: String(limit),
        offset: String(offset),
        ...(selectedTopic && { topic: selectedTopic }),
      }),
  });

  const { data: countData } = useQuery({
    queryKey: ["statements-count"],
    queryFn: () => api.getStatementCount(),
  });

  const statements = data?.data || [];
  const total = countData?.data?.count || 0;

  const { data: topicsData } = useQuery({
    queryKey: ["topics"],
    queryFn: () => api.getTopics(),
  });
  const topics = topicsData?.data || [];

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-2 mb-2">
          <FileText size={20} className="text-green-700" />
          <h1 className="text-2xl font-bold text-gray-900">
            Verified Statements
          </h1>
        </div>
        <p className="text-gray-600">
          {total > 0
            ? `${total} verified statements from Kerala ministers and MLAs`
            : "Verified statements from Kerala ministers and MLAs"}
        </p>
      </div>

      {/* Topic filters */}
      {topics.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-6">
          <button
            onClick={() => {
              setSelectedTopic("");
              setOffset(0);
            }}
            className={`text-sm px-3 py-1.5 rounded-full border transition-colors ${
              !selectedTopic
                ? "bg-green-700 text-white border-green-700"
                : "border-gray-200 text-gray-600 hover:border-green-400"
            }`}
          >
            All
          </button>
          {topics.map((t: { topic: string; count: number }) => (
            <button
              key={t.topic}
              onClick={() => {
                setSelectedTopic(t.topic);
                setOffset(0);
              }}
              className={`text-sm px-3 py-1.5 rounded-full border transition-colors ${
                selectedTopic === t.topic
                  ? "bg-green-700 text-white border-green-700"
                  : "border-gray-200 text-gray-600 hover:border-green-400"
              }`}
            >
              {t.topic} ({t.count})
            </button>
          ))}
        </div>
      )}

      {/* Statements */}
      {isLoading ? (
        <div className="space-y-4">
          {[...Array(5)].map((_, i) => (
            <div
              key={i}
              className="border border-gray-200 rounded-lg p-5 animate-pulse"
            >
              <div className="h-4 bg-gray-200 rounded w-32 mb-3" />
              <div className="h-16 bg-gray-200 rounded mb-3" />
              <div className="h-3 bg-gray-200 rounded w-48" />
            </div>
          ))}
        </div>
      ) : statements.length === 0 ? (
        <div
          className="text-center py-16 border border-gray-200
          rounded-lg bg-gray-50"
        >
          <FileText size={40} className="text-gray-300 mx-auto mb-3" />
          <p className="text-gray-600 font-medium">
            No approved statements yet
          </p>
          <p className="text-gray-500 text-sm mt-1">
            Statements are being reviewed by moderators.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {statements.map((statement: Record<string, unknown>) => (
            <StatementCard
              key={statement.id as number}
              statement={
                statement as unknown as Parameters<
                  typeof StatementCard
                >[0]["statement"]
              }
            />
          ))}
        </div>
      )}

      {/* Pagination */}
      {total > limit && (
        <div
          className="flex items-center justify-between mt-8
          pt-4 border-t border-gray-200"
        >
          <p className="text-sm text-gray-500">
            Showing {offset + 1}–{Math.min(offset + limit, total)} of {total}
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => setOffset(Math.max(0, offset - limit))}
              disabled={offset === 0}
              className="flex items-center gap-1 px-3 py-1.5 text-sm
                border border-gray-200 rounded-lg disabled:opacity-50
                hover:bg-gray-50"
            >
              <ChevronLeft size={14} />
              Previous
            </button>
            <button
              onClick={() => setOffset(offset + limit)}
              disabled={offset + limit >= total}
              className="flex items-center gap-1 px-3 py-1.5 text-sm
                border border-gray-200 rounded-lg disabled:opacity-50
                hover:bg-gray-50"
            >
              Next
              <ChevronRight size={14} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
