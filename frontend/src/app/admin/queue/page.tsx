"use client";

import { useState, useEffect, useTransition, Suspense, useCallback } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";
import { useRouter, useSearchParams } from "next/navigation";
import {
  ExternalLink,
  CheckCircle,
  XCircle,
  Loader2,
  RefreshCw,
  Zap,
  AlertCircle,
  FileText,
  Trash2,
  ChevronLeft,
  ChevronRight,
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

const PAGE_SIZE = 10;

const VALID_TABS = [
  "pending_review",
  "mining",
  "mined",
  "mining_failed",
  "rejected",
] as const;

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

function QueuePageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [, startTransition] = useTransition();
  const { isLoaded, isLoggedIn, isModerator } = useAuth();
  const queryClient = useQueryClient();
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [pollingIds, setPollingIds] = useState<Set<number>>(new Set());
  const canLoadQueue = isLoaded && isLoggedIn && isModerator;

  // Derive tab and page from URL
  const tabParam = searchParams.get("tab") ?? "pending_review";
  const activeTab = VALID_TABS.includes(tabParam as (typeof VALID_TABS)[number])
    ? tabParam
    : "pending_review";

  const pageParam = Number(searchParams.get("page") ?? "1");
  const page =
    Number.isInteger(pageParam) && pageParam >= 1 ? pageParam - 1 : 0;

  // Helper: push tab and page into the URL
  const navigate = useCallback(
    (tab: string, p: number) => {
      const params = new URLSearchParams();
      params.set("tab", tab);
      if (p > 0) params.set("page", String(p + 1)); // omit page=1 so that URLs are clean
      startTransition(() => {
        router.replace(`/admin/queue?${params.toString()}`, { scroll: false });
      });
      setSelectedIds(new Set());
    },
    [router, startTransition],
  );

  useEffect(() => {
    if (isLoaded && !isLoggedIn) {
      router.replace("/login");
    }
  }, [isLoaded, isLoggedIn, router]);

  // Stats
  const { data: statsData, refetch: refetchStats } = useQuery({
    queryKey: ["queue-stats"],
    queryFn: () => api.getQueueStats(),
    enabled: canLoadQueue,
    refetchInterval: 15000,
  });
  const stats = statsData?.data || {};

  // Queue items
  const {
    data: queueData,
    isLoading,
    refetch,
  } = useQuery({
    queryKey: ["queue", activeTab, page],
    queryFn: () =>
      api.getQueuePending({
        status: activeTab,
        limit: String(PAGE_SIZE),
        offset: String(page * PAGE_SIZE),
      }),
    enabled: canLoadQueue,
    refetchInterval: activeTab === "mining" ? 5000 : 30000,
  });

  const queuePayload = queueData?.data;

  const items: QueueItem[] = Array.isArray(queuePayload)
    ? queuePayload
    : queuePayload?.items || [];

  const total: number = Array.isArray(queuePayload)
    ? queuePayload.length
    : (queuePayload?.total ?? 0);

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const firstItem = total === 0 ? 0 : page * PAGE_SIZE + 1;
  const lastItem = Math.min(total, (page + 1) * PAGE_SIZE);
  const selectableItems = items.filter((item) => item.status !== "mining");
  const selectedItems = items.filter((item) => selectedIds.has(item.id));
  const selectedPendingItems = selectedItems.filter(
    (item) => item.status === "pending_review",
  );

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

  // Reject batch
  const rejectBatchMutation = useMutation({
    mutationFn: (ids: number[]) => api.rejectBatch(ids),
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

  // Delete item
  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.deleteQueueItem(id),
    onSuccess: () => {
      setSelectedIds(new Set());
      // If we deleted the last item on a page > 0, go back one page
      if (items.length === 1 && page > 0) {
        navigate(activeTab, page - 1);
      } else {
        queryClient.invalidateQueries({ queryKey: ["queue"] });
        queryClient.invalidateQueries({ queryKey: ["queue-stats"] });
      }
    },
  });

  const deleteBatchMutation = useMutation({
    mutationFn: (ids: number[]) => api.deleteBatch(ids),
    onSuccess: (_, ids) => {
      // If we deleted everything on this page and it's not page 0, go back
      if (ids.length >= items.length && page > 0) {
        navigate(activeTab, page - 1);
      } else {
        setSelectedIds(new Set());
        queryClient.invalidateQueries({ queryKey: ["queue"] });
        queryClient.invalidateQueries({ queryKey: ["queue-stats"] });
      }
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
    enabled: canLoadQueue && pollingIds.size > 0,
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
    setSelectedIds(new Set(selectableItems.map((item) => item.id)));
  };

  if (!isLoaded || !isLoggedIn) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="animate-spin text-gray-400" size={24} />
      </div>
    );
  }

  if (!isModerator) {
    return (
      <div className="text-center py-16">
        <p className="text-red-600 font-medium">Access denied.</p>
        <p className="text-gray-500 text-sm mt-1">
          You need moderator access to view the article queue.
        </p>
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
    { key: "mining_failed", label: "Failed", count: stats.mining_failed || 0 },
    { key: "rejected", label: "Rejected", count: stats.rejected || 0 },
  ];

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-white-100">Article Queue</h1>
          <p className="text-sm text-gray-400 mt-0.5">
            Review incoming articles and decide what gets mined
          </p>
        </div>
        <div className="flex items-center gap-2">
          {selectedIds.size > 0 && (
            <>
              {selectedPendingItems.length > 0 && (
                <>
                  <button
                    onClick={() =>
                      mineBatchMutation.mutate(
                        selectedPendingItems.map((item) => item.id),
                      )
                    }
                    disabled={mineBatchMutation.isPending}
                    className="flex items-center gap-1.5 bg-green-700
                      text-white px-3 py-1.5 rounded-lg text-sm font-medium
                      hover:bg-green-800 disabled:opacity-50"
                  >
                    <Zap size={14} />
                    Mine {selectedPendingItems.length} selected
                  </button>
                  <button
                    onClick={() => {
                      const shouldReject = window.confirm(
                        `Reject ${selectedPendingItems.length} selected article${
                          selectedPendingItems.length !== 1 ? "s" : ""
                        }?`,
                      );
                      if (shouldReject) {
                        rejectBatchMutation.mutate(
                          selectedPendingItems.map((item) => item.id),
                        );
                      }
                    }}
                    disabled={rejectBatchMutation.isPending}
                    className="flex items-center gap-1.5 border border-gray-200
                      text-gray-600 px-3 py-1.5 rounded-lg text-sm font-medium
                      hover:bg-gray-50 disabled:opacity-50"
                  >
                    <XCircle size={14} />
                    Reject {selectedPendingItems.length}
                  </button>
                </>
              )}
              <button
                onClick={() => {
                  const shouldDelete = window.confirm(
                    `Remove ${selectedIds.size} selected article${
                      selectedIds.size !== 1 ? "s" : ""
                    } from the queue? They will not be picked up again.`,
                  );
                  if (shouldDelete) {
                    deleteBatchMutation.mutate([...selectedIds]);
                  }
                }}
                disabled={deleteBatchMutation.isPending}
                className="flex items-center gap-1.5 border border-red-200
                  text-red-600 px-3 py-1.5 rounded-lg text-sm font-medium
                  hover:bg-red-50 disabled:opacity-50"
              >
                {deleteBatchMutation.isPending ? (
                  <Loader2 size={14} className="animate-spin" />
                ) : (
                  <Trash2 size={14} />
                )}
                Remove {selectedIds.size}
              </button>
            </>
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
            onClick={() => navigate(tab.key, 0)}
            className={cn(
              "flex items-center gap-1.5 px-4 py-2 text-sm",
              "font-medium border-b-2 transition-colors -mb-px",
              activeTab === tab.key
                ? "border-green-700 text-green-700"
                : "border-transparent text-gray-500 hover:text-gray-700",
            )}
          >
            {tab.label}
            {tab.count > 0 && (
              <span
                className={cn(
                  "text-xs px-1.5 py-0.5 rounded-full",
                  activeTab === tab.key
                    ? "bg-green-100 text-green-700"
                    : "bg-gray-100 text-gray-500",
                )}
              >
                {tab.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Select all bar */}
      {selectableItems.length > 0 && (
        <div className="flex items-center gap-3 mb-3 text-sm text-white-100">
          <button
            onClick={selectAll}
            className="hover:text-green-600 transition-colors"
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
        <div
          className="text-center py-16 border border-gray-200
          rounded-lg bg-gray-50"
        >
          <FileText size={36} className="text-gray-300 mx-auto mb-3" />
          <p className="text-gray-600 font-medium">No items in this queue</p>
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
              activeTab={activeTab}
              currentPage={page}
              isSelected={selectedIds.has(item.id)}
              isMining={pollingIds.has(item.id)}
              canSelect={item.status !== "mining"}
              onSelect={() => toggleSelect(item.id)}
              onMine={() => mineMutation.mutate(item.id)}
              onReject={() => rejectMutation.mutate(item.id)}
              onDelete={() => {
                const shouldDelete = window.confirm(
                  "Remove this article from the queue? It will not be picked up again in future batches.",
                );
                if (shouldDelete) deleteMutation.mutate(item.id);
              }}
              isMineLoading={
                mineMutation.isPending && mineMutation.variables === item.id
              }
              isDeleteLoading={
                deleteMutation.isPending && deleteMutation.variables === item.id
              }
            />
          ))}
        </div>
      )}

      {/* Pagination */}
      {total > PAGE_SIZE && (
        <div className="flex items-center justify-between gap-3 mt-5 text-sm">
          <p className="text-gray-500">
            Showing {firstItem}-{lastItem} of {total}
          </p>

          <GoToPageInput
            key={page}
            page={page}
            totalPages={totalPages}
            onNavigate={(target) => navigate(activeTab, target)}
          />

          <div className="flex items-center gap-2">
            <button
              onClick={() => navigate(activeTab, page - 1)}
              disabled={page === 0}
              className="flex items-center gap-1.5 border border-gray-200
                text-gray-600 px-3 py-1.5 rounded-lg font-medium
                hover:bg-gray-50 disabled:opacity-50 disabled:hover:bg-white"
            >
              <ChevronLeft size={14} />
              Previous
            </button>
            <span className="text-gray-500">
              Page {page + 1} of {totalPages}
            </span>
            <button
              onClick={() => navigate(activeTab, page + 1)}
              disabled={page >= totalPages - 1}
              className="flex items-center gap-1.5 border border-gray-200
                text-gray-600 px-3 py-1.5 rounded-lg font-medium
                hover:bg-gray-50 disabled:opacity-50 disabled:hover:bg-white"
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

export default function QueuePage() {
  return (
    <Suspense
      fallback={
        <div className="flex items-center justify-center min-h-[60vh]">
          <Loader2 className="animate-spin text-gray-400" size={24} />
        </div>
      }
    >
      <QueuePageContent />
    </Suspense>
  );
}

interface GoToPageInputProps {
  page: number;
  totalPages: number;
  onNavigate: (targetPageIndex: number) => void;
}

function GoToPageInput({ page, totalPages, onNavigate }: GoToPageInputProps) {
  const [pageInput, setPageInput] = useState(String(page + 1));

  const commit = () => {
    const target = Number(pageInput.trim());
    if (Number.isInteger(target) && target >= 1 && target <= totalPages) {
      onNavigate(target - 1);
    } else {
      // Invalid input go back to the current page.
      setPageInput(String(page + 1));
    }
  };

  return (
    <div className="flex items-center gap-2">
      <span>Go to page</span>
      <input
        type="number"
        min={1}
        max={totalPages}
        value={pageInput}
        onChange={(e) => setPageInput(e.target.value)}
        onBlur={commit}
        onKeyDown={(e) => {
          if (e.key === "Enter") commit();
        }}
        className="w-20 border rounded px-2 py-1"
      />
      <button onClick={commit}>Go</button>
    </div>
  );
}


// Queue Item Card
interface QueueItemCardProps {
  item: QueueItem;
  activeTab: string;
  currentPage: number;
  isSelected: boolean;
  isMining: boolean;
  canSelect: boolean;
  onSelect: () => void;
  onMine: () => void;
  onReject: () => void;
  onDelete: () => void;
  isMineLoading: boolean;
  isDeleteLoading: boolean;
}

function QueueItemCard({
  item,
  activeTab,
  currentPage,
  isSelected,
  isMining,
  canSelect,
  onSelect,
  onMine,
  onReject,
  onDelete,
  isMineLoading,
  isDeleteLoading,
}: QueueItemCardProps) {
  const isPending = item.status === "pending_review";
  const isMiningStatus = item.status === "mining" || isMining;
  const isMined = item.status === "mined";
  const isFailed = item.status === "mining_failed";
  const canDelete = item.status !== "mining" && !isMining;

  // Build review link so the back-button can restore the exact page
  const reviewHref = `/admin/queue/${item.id}?from_tab=${activeTab}${
    currentPage > 0 ? `&from_page=${currentPage + 1}` : ""
  }`;

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
        {canSelect && (
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
                href={reviewHref}
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
                <span className="flex items-center gap-1 text-xs text-red-600">
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
              <span className="flex items-center gap-1.5 text-xs text-blue-600">
                <Loader2 size={12} className="animate-spin" />
                Processing with LLM...
              </span>
            )}

            {canDelete && (
              <button
                onClick={onDelete}
                disabled={isDeleteLoading}
                className="flex items-center gap-1.5 border border-red-200
                  text-red-600 px-3 py-1.5 rounded-lg text-xs font-medium
                  hover:bg-red-50 disabled:opacity-50"
              >
                {isDeleteLoading ? (
                  <Loader2 size={12} className="animate-spin" />
                ) : (
                  <Trash2 size={12} />
                )}
                Delete
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
