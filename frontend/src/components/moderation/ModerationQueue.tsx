"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../lib/api";
import StatementCard from "./StatementCard";
import { RefreshCw, Filter } from "lucide-react";
import type { StatementCardProps } from "./StatementCard";

export default function ModerationQueue() {
  const [offset, setOffset] = useState(0);
  const [minConfidence, setMinConfidence] = useState("");
  const limit = 10;

  const { data, isLoading, refetch, isFetching } = useQuery({
    queryKey: ["moderation-queue", offset, minConfidence],
    queryFn: () =>
      api.getModerationQueue({
        limit: String(limit),
        offset: String(offset),
        ...(minConfidence && { min_confidence: minConfidence }),
      }),
  });

  const queue = data?.data;
  const total = queue?.total || 0;
  const statements = queue?.statements || [];

  return (
    <div>
      {/* Toolbar */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <h2 className="font-semibold text-foreground">
            Review Queue
            {total > 0 && (
              <span className="ml-2 text-sm font-normal text-muted">
                ({total} pending)
              </span>
            )}
          </h2>
        </div>

        <div className="flex items-center gap-2">
          {/* Confidence filter */}
          <div className="flex items-center gap-1.5">
            <Filter size={14} className="text-muted-2" />
            <select
              value={minConfidence}
              onChange={(e) => {
                setMinConfidence(e.target.value);
                setOffset(0);
              }}
              className="text-sm border border-border bg-surface text-foreground rounded-lg px-2
                py-1.5 focus:outline-none focus:border-accent cursor-pointer"
            >
              <option value="">All confidence</option>
              <option value="0.8">High (80%+)</option>
              <option value="0.6">Medium (60%+)</option>
              <option value="0.45">Low (45%+)</option>
            </select>
          </div>

          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className="flex items-center gap-1.5 text-sm text-muted
              border border-border px-3 py-1.5 rounded-lg
              hover:bg-surface-2 hover:text-foreground disabled:opacity-50 transition-colors"
          >
            <RefreshCw size={14} className={isFetching ? "animate-spin" : ""} />
            Refresh
          </button>
        </div>
      </div>

      {/* Queue */}
      {isLoading ? (
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <div
              key={i}
              className="border border-border bg-surface rounded-xl p-5 shadow-sm animate-pulse"
            >
              <div className="h-4 bg-surface-2 rounded w-32 mb-3" />
              <div className="h-16 bg-surface-2 rounded mb-3" />
              <div className="h-3 bg-surface-2 rounded w-48" />
            </div>
          ))}
        </div>
      ) : statements.length === 0 ? (
        <div className="text-center py-16 text-muted">
          <p className="text-lg font-medium mb-1 text-foreground">
            Queue is empty
          </p>
          <p className="text-sm">No pending statements match your filters.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {statements.map((statement: Record<string, unknown>) => (
            <StatementCard
              key={statement.id as number}
              statement={statement as StatementCardProps["statement"]}
            />
          ))}
        </div>
      )}

      {/* Pagination */}
      {total > limit && (
        <div
          className="flex items-center justify-between mt-6 pt-4
          border-t border-border"
        >
          <p className="text-sm text-muted">
            Showing {offset + 1}–{Math.min(offset + limit, total)} of {total}
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => setOffset(Math.max(0, offset - limit))}
              disabled={offset === 0}
              className="px-3 py-1.5 text-sm text-foreground border border-border
                rounded-lg disabled:opacity-40 hover:bg-surface-2 transition-colors"
            >
              Previous
            </button>
            <button
              onClick={() => setOffset(offset + limit)}
              disabled={offset + limit >= total}
              className="px-3 py-1.5 text-sm text-foreground border border-border
                rounded-lg disabled:opacity-40 hover:bg-surface-2 transition-colors"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
