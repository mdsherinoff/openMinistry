"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import StatementCard from "@/components/StatementCard";
import { StatementSkeleton } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { FileText, ChevronLeft, ChevronRight } from "lucide-react";

export default function VerifiedStatementsPage() {
  const [offset, setOffset] = useState(0);
  const [selectedTopic, setSelectedTopic] = useState("");
  const limit = 10;

  const { data, isLoading, isError, refetch } = useQuery({
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
    queryKey: ["statements-count", selectedTopic],
    queryFn: () =>
      api.getStatementCount({
        status: "approved",
        ...(selectedTopic && { topic: selectedTopic }),
      }),
  });

  const { data: topicsData } = useQuery({
    queryKey: ["topics"],
    queryFn: () => api.getTopics(),
  });

  const statements = data?.data || [];
  const total = countData?.data?.count || 0;
  const topics = topicsData?.data || [];

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-1">
          <FileText size={20} className="text-green-700" />
          <h1 className="text-2xl font-bold text-white-10">
            Verified Statements
          </h1>
        </div>
        <p className="text-gray-500 text-sm max-w-3xl">
          Browse verified statements made by Kerala ministers and MLAs,
          collected from newspapers, reviewed by human moderators, and published
          in an open public archive.
        </p>
        <p className="text-gray-500 text-sm">
          {total > 0
            ? `${total} verified statement${total !== 1 ? "s" : ""}
              ${selectedTopic ? `tagged ${selectedTopic}` : ""}`
            : "Human-verified statements from Kerala ministers and MLAs"}
        </p>
      </div>

      {/* Topic filters */}
      {topics.length > 0 && (
        <div className="mb-6">
          <select
            value={selectedTopic}
            onChange={(e) => {
              setSelectedTopic(e.target.value);
              setOffset(0);
            }}
            className="text-sm px-3 py-1.5 rounded-lg border border-gray-200 
        text-gray-600 bg-white hover:border-green-400 
        focus:outline-none focus:border-green-700 transition-colors"
          >
            <option value="">All Topics</option>
            {topics.map((t: { topic: string; count: number }) => (
              <option key={t.topic} value={t.topic}>
                {t.topic} ({t.count})
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Content */}
      {isError ? (
        <ErrorState message="Could not load statements" onRetry={refetch} />
      ) : isLoading ? (
        <div className="space-y-4">
          {[...Array(5)].map((_, i) => (
            <StatementSkeleton key={i} />
          ))}
        </div>
      ) : statements.length === 0 ? (
        <EmptyState
          icon={FileText}
          title="No statements found"
          description={
            selectedTopic
              ? `No verified statements tagged as ${selectedTopic} yet.`
              : "No verified statements yet. Check back soon."
          }
          action={
            selectedTopic
              ? { label: "View all statements", href: "/statements" }
              : undefined
          }
        />
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
      {total > limit && !isLoading && !isError && (
        <div
          className="flex items-center justify-between mt-8
          pt-4 border-t border-gray-200"
        >
          <p className="text-sm text-gray-500">
            Showing {offset + 1}-{Math.min(offset + limit, total)} of {total}
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => setOffset(Math.max(0, offset - limit))}
              disabled={offset === 0}
              className="flex items-center gap-1 px-3 py-1.5 text-sm
                border border-gray-200 rounded-lg disabled:opacity-50
                hover:bg-gray-50 transition-colors"
            >
              <ChevronLeft size={14} />
              Previous
            </button>
            <button
              onClick={() => setOffset(offset + limit)}
              disabled={offset + limit >= total}
              className="flex items-center gap-1 px-3 py-1.5 text-sm
                border border-gray-200 rounded-lg disabled:opacity-50
                hover:bg-gray-50 transition-colors"
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
