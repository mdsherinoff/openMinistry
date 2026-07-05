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
      <header
        className="mb-6 overflow-hidden rounded-2xl border border-border
        bg-surface p-6 sm:p-8"
      >
        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-foreground">
          Verified Statements
        </h1>
        <p className="text-muted text-base leading-relaxed max-w-2xl mt-2">
          Statements made by Kerala ministers and MLAs, collected from
          newspapers, reviewed by human moderators, and published in an open
          public archive.
        </p>
        <p className="text-muted-2 text-xs mt-3">
          {total > 0
            ? `${total.toLocaleString("en-IN")} verified statement${
                total !== 1 ? "s" : ""
              }${selectedTopic ? ` tagged ${selectedTopic}` : ""}`
            : "No verified statements yet"}
        </p>
      </header>

      {/* Topic filters */}
      {topics.length > 0 && (
        <div className="mb-6">
          <select
            value={selectedTopic}
            onChange={(e) => {
              setSelectedTopic(e.target.value);
              setOffset(0);
            }}
            className="text-sm px-3 py-2 rounded-lg border border-border
        text-foreground bg-surface hover:border-accent-border
        focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent
        transition-colors cursor-pointer"
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
          pt-4 border-t border-border"
        >
          <p className="text-sm text-muted">
            Showing {offset + 1}-{Math.min(offset + limit, total)} of {total}
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => setOffset(Math.max(0, offset - limit))}
              disabled={offset === 0}
              className="flex items-center gap-1 px-3 py-1.5 text-sm font-medium
                text-foreground border border-border rounded-lg disabled:opacity-40
                disabled:cursor-not-allowed hover:bg-surface-2 hover:border-accent-border
                transition-colors"
            >
              <ChevronLeft size={14} />
              Previous
            </button>
            <button
              onClick={() => setOffset(offset + limit)}
              disabled={offset + limit >= total}
              className="flex items-center gap-1 px-3 py-1.5 text-sm font-medium
                text-foreground border border-border rounded-lg disabled:opacity-40
                disabled:cursor-not-allowed hover:bg-surface-2 hover:border-accent-border
                transition-colors"
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
