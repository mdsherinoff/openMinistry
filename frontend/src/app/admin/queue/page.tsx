"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";
import { useRouter } from "next/navigation";
import {
  ExternalLink, CheckCircle, XCircle,
  Clock, Loader2, RefreshCw, Zap,
  AlertCircle, FileText, BarChart2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import Link from "next/link";

interface QueueItem {
  id: number;
  url: string;
  title: string | null;
  source_name: string | null;
  status: string;
  statements_found: number;
  mining_error: string | null;
  created_at: string;
  reviewed_at: string | null;
}

const STATUS_COLORS: Record<string, string> = {
  pending_review: "bg-amber-50 text-amber-700 border-amber-200",
  mining: "bg-blue-50 text-blue-700 border-blue-200",
  mined: "bg-green-50 text-green-700 border-green-200",
  mining_failed: "bg-red-50 text-red-700 border-red-200",
  rejected: "bg-gray-100 text-gray-500 border-gray-200",
};

const STATUS_LABELS: Record<string, string> = {
  pending_review: "Pending Review",
  mining: "Mining...",
  mined: "Mined",
  mining_failed: "Failed",
  rejected: "Rejected",
};

export default function QueuePage() {
  const router = useRouter();
  const { isLoaded, isLoggedIn, isModerator } = useAuth();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState("pending_review");
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [pollingIds, setPollingIds] = useState<Set<number>>(new Set());

  useEffect(() => {
    if (isLoaded && !isLoggedIn) router.push("/login");
  }, [isLoaded, isLoggedIn, router]);

  // Stats
  const { data: statsData, refetch: refetchStats } = useQuery({
    queryKey: ["queue-stats"],
    queryFn: () => api.getQueueStats(),
    refetchInterval: 15000,
  });
  const stats = statsData?.data || {};

  // Queue items
  const { data: queueData, isLoading, refetch } = useQuery({
    queryKey: ["queue", activeTab],
    queryFn: () =>
      api.getQueuePending({ status: activeTab, limit: "100" }),
    refetchInterval: activeTab === "mining" ? 5000 : 30000,
  });
  const items: QueueItem[] = queueData?.data || [];

  // Mine single item
  const mineMutation = useMutation({
    mutationFn: (id: number) => api.approveForMining(id),
    onSuccess: (_, id) => {
      setPollingIds((prev) => new Set([...prev, id]));
      queryClient.invalidateQueries({ queryKey: ["queue"] });
      queryClient.invalidateQueries({ queryKey: ["queue-stats"] });
    },
  });

  // Mine batch
  const mineBatchMutation = useMutation({
    mutationFn: (ids: number[]) => api.mineBatch(ids),
    onSuccess: () => {
      setSelectedIds(new Set());
      queryClient.invalidateQueries({ queryKey: ["queue"] });
      queryClient.invalidateQueries({ queryKey: ["queue-stats"] });
    },
  });

  // Reject item
  const rejectMutation = useMutation({
    mutationFn: (id: number) => api.rejectQueueItem(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["queue"] });
      queryClient.invalidateQueries({ queryKey: ["queue-stats"] });
    },
  });

  // Poll mining items
  useQuery({
    queryKey: ["mining-poll", [...pollingIds].join(",")],
    queryFn: async () => {
      const done = new Set<number>();
      for (const id of pollingIds) {
        const res = await api.getMiningStatus(id);
        const status = res.data?.status;
        if (status === "mined" || status === "mining_failed") {
          done.add(id);
        }
      }
      if (done.size > 0) {
        setPollingIds((prev) => {
          const next = new Set(prev);
          done.forEach((id) => next.delete(id));
          return next;
        });
        queryClient.invalidateQueries({ queryKey: ["queue"] });
        queryClient.invalidateQueries({ queryKey: ["queue-stats"] });
      }
      return null;
    },
    enabled: pollingIds.size > 0,
    refetchInterval: 3000,
  });

  const toggleSelect = (id: number) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const selectAll = () => {
    const pendingIds = items
      .filter((i) => i.status === "pending_review")
      .map((i) => i.id);
    setSelectedIds(new Set(pendingIds));
  };

  if (!isLoaded || !isLoggedIn || !isModerator) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="animate-spin text-gray-400" size={24} />
      </div>
    );
  }

  const tabs = [
    {
      key: "pending_review",
      label: "Pending",
      count: stats.pending_review || 0,
    },
    { key: "mining", label: "Mining", count: stats.mining || 0 },
    { key: "mined", label: "Mined", count: stats.mined || 0 },
    {
      key: "mining_failed",
      label: "Failed",
      count: stats.mining_failed || 0,
    },
    { key: "rejected", label: "Rejected", count: stats.rejected || 0 },
  ];

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-white-100">
            Article Queue
          </h1>
          <p className="text-sm text-gray-400 mt-0.5">
            Review incoming articles and decide what gets mined
          </p>
        </div>
        <div className="flex items-center gap-2">
          {selectedIds.size > 0 && (
            <button
              onClick={() =>
                mineBatchMutation.mutate([...selectedIds])
              }
              disabled={mineBatchMutation.isPending}
              className="flex items-center gap-1.5 bg-green-700
                text-white px-3 py-1.5 rounded-lg text-sm font-medium
                hover:bg-green-800 disabled:opacity-50"
            >
              <Zap size={14} />
              Mine {selectedIds.size} selected
            </button>
          )}
          <button
            onClick={() => {
              refetch();
              refetchStats();
            }}
            className="flex items-center gap-1.5 border border-gray-200
              text-gray-600 px-3 py-1.5 rounded-lg text-sm
              hover:bg-gray-50"
          >
            <RefreshCw size={14} />
            Refresh
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 mb-4 border-b border-gray-200">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => {
              setActiveTab(tab.key);
              setSelectedIds(new Set());
            }}
            className={cn(
              "flex items-center gap-1.5 px-4 py-2 text-sm",
              "font-medium border-b-2 transition-colors -mb-px",
              activeTab === tab.key
                ? "border-green-700 text-green-700"
                : "border-transparent text-gray-500 hover:text-gray-700"
            )}
          >
            {tab.label}
            {tab.count > 0 && (
              <span
                className={cn(
                  "text-xs px-1.5 py-0.5 rounded-full",
                  activeTab === tab.key
                    ? "bg-green-100 text-green-700"
                    : "bg-gray-100 text-gray-500"
                )}
              >
                {tab.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Select all bar */}
      {activeTab === "pending_review" && items.length > 0 && (
        <div className="flex items-center gap-3 mb-3 text-sm text-gray-600">
          <button
            onClick={selectAll}
            className="hover:text-green-700 transition-colors"
          >
            Select all
          </button>
          {selectedIds.size > 0 && (
            <button
              onClick={() => setSelectedIds(new Set())}
              className="hover:text-red-600 transition-colors"
            >
              Clear selection
            </button>
          )}
        </div>
      )}

      {/* Queue items */}
      {isLoading ? (
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <div
              key={i}
              className="border border-gray-200 rounded-lg p-4
                animate-pulse bg-white"
            >
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-2" />
              <div className="h-3 bg-gray-200 rounded w-1/2" />
            </div>
          ))}
        </div>
      ) : items.length === 0 ? (
        <div className="text-center py-16 border border-gray-200
          rounded-lg bg-gray-50">
          <FileText size={36} className="text-gray-300 mx-auto mb-3" />
          <p className="text-gray-600 font-medium">
            No items in this queue
          </p>
          <p className="text-gray-500 text-sm mt-1">
            {activeTab === "pending_review"
              ? "URLs will appear here automatically every 30 minutes"
              : "Nothing here yet"}
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {items.map((item) => (
            <QueueItemCard
              key={item.id}
              item={item}
              isSelected={selectedIds.has(item.id)}
              isMining={pollingIds.has(item.id)}
              onSelect={() => toggleSelect(item.id)}
              onMine={() => mineMutation.mutate(item.id)}
              onReject={() => rejectMutation.mutate(item.id)}
              isMineLoading={
                mineMutation.isPending &&
                mineMutation.variables === item.id
              }
            />
          ))}
        </div>
      )}
    </div>
  );
}

interface QueueItemCardProps {
  item: QueueItem;
  isSelected: boolean;
  isMining: boolean;
  onSelect: () => void;
  onMine: () => void;
  onReject: () => void;
  isMineLoading: boolean;
}

function QueueItemCard({
  item,
  isSelected,
  isMining,
  onSelect,
  onMine,
  onReject,
  isMineLoading,
}: QueueItemCardProps) {
  const isPending = item.status === "pending_review";
  const isMiningStatus =
    item.status === "mining" || isMining;
  const isMined = item.status === "mined";
  const isFailed = item.status === "mining_failed";

  return (
    <div
      className={cn(
        "border rounded-lg p-4 bg-white transition-all",
        isSelected
          ? "border-green-400 bg-green-50"
          : "border-gray-200 hover:border-gray-300",
      )}
    >
      <div className="flex items-start gap-3">
        {/* Checkbox */}
        {isPending && (
          <input
            type="checkbox"
            checked={isSelected}
            onChange={onSelect}
            className="mt-1 rounded border-gray-300
              text-green-700 focus:ring-green-500"
          />
        )}

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-3 mb-1">
            <p className="font-medium text-gray-900 text-sm leading-snug">
              {item.title || "No title available"}
            </p>
            <span
              className={cn(
                "text-xs px-2 py-0.5 rounded-full border",
                "whitespace-nowrap flex-shrink-0",
                STATUS_COLORS[item.status] || "bg-gray-100 text-gray-500",
              )}
            >
              {isMiningStatus && item.status === "mining" ? (
                <span className="flex items-center gap-1">
                  <Loader2 size={10} className="animate-spin" />
                  Mining...
                </span>
              ) : (
                STATUS_LABELS[item.status] || item.status
              )}
            </span>
          </div>

          <div className="flex items-center gap-3 text-xs text-gray-500 mb-3">
            <span>{item.source_name || "Unknown source"}</span>
            <span>•</span>
            <span>
              {new Date(item.created_at).toLocaleDateString("en-IN", {
                day: "numeric",
                month: "short",
                hour: "2-digit",
                minute: "2-digit",
              })}
            </span>

            <a
              href={item.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-0.5 text-green-700 hover:underline"
              onClick={(e) => e.stopPropagation()}
            >
              View article <ExternalLink size={10} />
            </a>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2">
            {isPending && (
              <>
                <button
                  onClick={onMine}
                  disabled={isMineLoading}
                  className="flex items-center gap-1.5 bg-green-700
                    text-white px-3 py-1.5 rounded-lg text-xs
                    font-medium hover:bg-green-800 disabled:opacity-50"
                >
                  {isMineLoading ? (
                    <Loader2 size={12} className="animate-spin" />
                  ) : (
                    <Zap size={12} />
                  )}
                  Mine
                </button>
                <button
                  onClick={onReject}
                  className="flex items-center gap-1.5 border
                    border-gray-200 text-gray-600 px-3 py-1.5
                    rounded-lg text-xs font-medium hover:bg-gray-50"
                >
                  <XCircle size={12} />
                  Reject
                </button>
              </>
            )}

            {isMined && (
              <Link
                href={`/admin/queue/${item.id}`}
                className="flex items-center gap-1.5 bg-green-700
                  text-white px-3 py-1.5 rounded-lg text-xs
                  font-medium hover:bg-green-800"
              >
                <CheckCircle size={12} />
                Review {item.statements_found} statement
                {item.statements_found !== 1 ? "s" : ""}
              </Link>
            )}

            {isFailed && (
              <div className="flex items-center gap-2">
                <span
                  className="flex items-center gap-1 text-xs
                  text-red-600"
                >
                  <AlertCircle size={12} />
                  {item.mining_error?.slice(0, 60) || "Mining failed"}
                </span>
                <button
                  onClick={onMine}
                  className="text-xs text-green-700 hover:underline"
                >
                  Retry
                </button>
              </div>
            )}

            {isMiningStatus && item.status === "mining" && (
              <span
                className="flex items-center gap-1.5 text-xs
                text-blue-600"
              >
                <Loader2 size={12} className="animate-spin" />
                Processing with LLM...
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}