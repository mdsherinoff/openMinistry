"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";
import {
  ArrowLeft,
  ExternalLink,
  CheckCircle,
  XCircle,
  Edit,
  Plus,
  Loader2,
  User,
  ChevronDown,
  ChevronUp,
  Save,
  AlertCircle,
} from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";

interface MinedResult {
  id: number;
  queue_item_id: number;
  speaker_name: string | null;
  speaker_role: string | null;
  minister_id: number | null;
  statement_text: string;
  context_description: string | null;
  topic_tag: string | null;
  confidence_stars: number;
  status: string;
  edited_speaker_name: string | null;
  edited_statement_text: string | null;
  edited_topic: string | null;
  statement_id: number | null;
}

interface QueueItem {
  id: number;
  url: string;
  title: string | null;
  source_name: string | null;
  status: string;
  statements_found: number;
  created_at: string;
}

interface Minister {
  id: number;
  name: string;
  portfolio: string | null;
}

const TOPICS = [
  "Health",
  "Education",
  "Transport",
  "Economy",
  "Agriculture",
  "Environment",
  "Infrastructure",
  "Law & Order",
  "Social Welfare",
  "Politics",
  "Tourism",
  "Finance",
  "Sports",
  "Culture",
];

const CONFIDENCE_LABELS: Record<number, string> = {
  1: "Very Low",
  2: "Low",
  3: "Medium",
  4: "High",
  5: "Very High",
};

const CONFIDENCE_COLORS: Record<number, string> = {
  1: "text-red-600 bg-red-50",
  2: "text-orange-600 bg-orange-50",
  3: "text-amber-600 bg-amber-50",
  4: "text-blue-600 bg-blue-50",
  5: "text-green-600 bg-green-50",
};

export default function ReviewPage() {
  const params = useParams();
  const router = useRouter();
  const { isLoaded, isLoggedIn, isModerator } = useAuth();
  const queryClient = useQueryClient();
  const itemId = Number(params.id);

  useEffect(() => {
    if (isLoaded && !isLoggedIn) router.replace("/login");
  }, [isLoaded, isLoggedIn, router]);

  // Fetch queue item
  const { data: itemData, isLoading: itemLoading } = useQuery({
    queryKey: ["queue-item", itemId],
    queryFn: () => api.getQueueItem(itemId),
    enabled: !!itemId,
  });
  const item: QueueItem | null = itemData?.data || null;

  // Fetch mined results
  const { data: resultsData, isLoading: resultsLoading } = useQuery({
    queryKey: ["mined-results", itemId],
    queryFn: () => api.getMinedResults(itemId),
    enabled: !!itemId,
  });
  const results: MinedResult[] = resultsData?.data || [];

  // Fetch ministers for dropdown
  const { data: ministersData } = useQuery({
    queryKey: ["ministers-all"],
    queryFn: () => api.getMinisters(true),
  });
  const ministers: Minister[] = ministersData?.data || [];

  const pending = results.filter((r) => r.status === "awaiting_review");
  const approved = results.filter((r) => r.status === "approved");
  const rejected = results.filter((r) => r.status === "rejected");

  if (!isLoaded || !isLoggedIn || !isModerator) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="animate-spin text-gray-400" size={24} />
      </div>
    );
  }

  if (itemLoading || resultsLoading) {
    return (
      <div className="space-y-4">
        <div className="h-8 bg-gray-200 rounded w-48 animate-pulse" />
        {[...Array(3)].map((_, i) => (
          <div
            key={i}
            className="border border-gray-200 rounded-lg p-5 animate-pulse"
          >
            <div className="h-4 bg-gray-200 rounded w-32 mb-3" />
            <div className="h-16 bg-gray-200 rounded" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div>
      {/* Back */}
      <Link
        href="/admin/queue"
        className="flex items-center gap-1.5 text-sm text-white-100
          hover:text-gray-500 mb-4"
      >
        <ArrowLeft size={14} />
        Back to queue
      </Link>

      {/* Article header */}
      {item && (
        <div className="border border-gray-200 rounded-lg p-4 mb-6 bg-white">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h1 className="font-bold text-gray-900 mb-1">
                {item.title || "Untitled article"}
              </h1>
              <div className="flex items-center gap-3 text-sm text-gray-500">
                <span>{item.source_name}</span>
                <span>•</span>
                <span>
                  {new Date(item.created_at).toLocaleDateString("en-IN")}
                </span>
                <a
                  href={item.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1 text-green-700 hover:underline"
                >
                  Read original <ExternalLink size={12} />
                </a>
              </div>
            </div>
            <div className="flex items-center gap-2 text-sm flex-shrink-0">
              <span className="text-green-600 font-medium">
                {approved.length} approved
              </span>
              <span className="text-gray-400">·</span>
              <span className="text-amber-600 font-medium">
                {pending.length} pending
              </span>
              <span className="text-gray-400">·</span>
              <span className="text-red-500 font-medium">
                {rejected.length} rejected
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Results */}
      {results.length === 0 ? (
        <div
          className="text-center py-12 border border-gray-200
          rounded-lg bg-gray-50"
        >
          <AlertCircle size={36} className="text-gray-300 mx-auto mb-3" />
          <p className="text-gray-600 font-medium">No statements found</p>
          <p className="text-gray-500 text-sm mt-1">
            The miner did not find any political statements in this article.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {results.map((result) => (
            <MinedResultCard
              key={result.id}
              result={result}
              itemId={itemId}
              ministers={ministers}
              onUpdate={() => {
                queryClient.invalidateQueries({
                  queryKey: ["mined-results", itemId],
                });
                queryClient.invalidateQueries({
                  queryKey: ["queue-item", itemId],
                });
              }}
            />
          ))}
        </div>
      )}

      {/* Add manual statement */}
      <AddManualStatement
        itemId={itemId}
        ministers={ministers}
        onAdd={() => {
          queryClient.invalidateQueries({
            queryKey: ["mined-results", itemId],
          });
        }}
      />
    </div>
  );
}

// ─────────────────────────────────────────
// Mined Result Card
// ─────────────────────────────────────────

interface MinedResultCardProps {
  result: MinedResult;
  itemId: number;
  ministers: Minister[];
  onUpdate: () => void;
}

function MinedResultCard({
  result,
  itemId,
  ministers,
  onUpdate,
}: MinedResultCardProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [showContext, setShowContext] = useState(false);
  const [actionError, setActionError] = useState("");

  // Edit state
  const [text, setText] = useState(
    result.edited_statement_text || result.statement_text,
  );
  const [ministerId, setMinisterId] = useState(
    result.minister_id?.toString() || "",
  );
  const [topic, setTopic] = useState(
    result.edited_topic || result.topic_tag || "",
  );
  const [speakerName, setSpeakerName] = useState(
    result.edited_speaker_name || result.speaker_name || "",
  );

  const isApproved = result.status === "approved";
  const isRejected = result.status === "rejected";
  const isDone = isApproved || isRejected;

  // Save edits
  const saveMutation = useMutation({
    mutationFn: () =>
      api.updateMinedResult(itemId, result.id, {
        edited_statement_text: text,
        edited_speaker_name: speakerName,
        edited_topic: topic,
        minister_id: ministerId ? Number(ministerId) : null,
      }),
    onSuccess: () => {
      setActionError("");
      setIsEditing(false);
      onUpdate();
    },
    onError: (error: unknown) => {
      setActionError(
        (error as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || "Unable to save changes",
      );
    },
  });

  // Approve
  const approveMutation = useMutation({
    mutationFn: () =>
      api.approveMinedResult(itemId, result.id, {
        mined_result_id: result.id,
        statement_text: text,
        minister_id: ministerId ? Number(ministerId) : null,
        topic: topic || null,
        context_text: result.context_description || null,
      }),
    onSuccess: () => {
      setActionError("");
      onUpdate();
    },
    onError: (error: unknown) => {
      setActionError(
        (error as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || "Unable to approve statement",
      );
    },
  });

  // Reject
  const rejectMutation = useMutation({
    mutationFn: () => api.rejectMinedResult(itemId, result.id),
    onSuccess: () => {
      setActionError("");
      onUpdate();
    },
    onError: (error: unknown) => {
      setActionError(
        (error as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || "Unable to reject statement",
      );
    },
  });

  const isLoading =
    saveMutation.isPending ||
    approveMutation.isPending ||
    rejectMutation.isPending;

  return (
    <div
      className={cn(
        "border rounded-lg p-5 bg-white transition-all",
        isApproved && "border-green-300 bg-green-50/30",
        isRejected && "border-gray-200 opacity-60",
        !isDone && "border-gray-200",
      )}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <User size={14} className="text-gray-400 flex-shrink-0 mt-0.5" />
          <div>
            {isEditing ? (
              <input
                value={speakerName}
                onChange={(e) => setSpeakerName(e.target.value)}
                className="border border-gray-300 rounded px-2 py-1
                  text-sm font-medium focus:outline-none
                  focus:border-green-500"
                placeholder="Speaker name"
              />
            ) : (
              <span className="font-medium text-gray-900 text-sm">
                {result.edited_speaker_name ||
                  result.speaker_name ||
                  "Unknown speaker"}
              </span>
            )}
            {result.speaker_role && (
              <span className="text-xs text-gray-500 ml-2">
                {result.speaker_role}
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span
            className={cn(
              "text-xs px-2 py-0.5 rounded-full font-medium",
              CONFIDENCE_COLORS[result.confidence_stars] ||
                "text-gray-600 bg-gray-100",
            )}
          >
            {CONFIDENCE_LABELS[result.confidence_stars] || "Unknown"} confidence
          </span>
          {isApproved && (
            <span
              className="text-xs px-2 py-0.5 rounded-full
              bg-green-100 text-green-700 font-medium"
            >
              ✓ Approved
            </span>
          )}
          {isRejected && (
            <span
              className="text-xs px-2 py-0.5 rounded-full
              bg-gray-100 text-gray-500 font-medium"
            >
              Rejected
            </span>
          )}
        </div>
      </div>

      {/* Minister assignment */}
      <div className="mb-3">
        <label className="block text-xs font-medium text-gray-600 mb-1">
          Assigned minister
        </label>
        <select
          value={ministerId}
          onChange={(e) => setMinisterId(e.target.value)}
          disabled={isDone && !isEditing}
          className="w-full border border-gray-300 rounded-lg px-3 py-2
            text-sm focus:outline-none focus:border-green-500
            disabled:bg-gray-50 text-gray-600"
        >
          <option value="">— Not assigned —</option>
          {ministers.map((m) => (
            <option key={m.id} value={m.id.toString()}>
              {m.name}
              {m.portfolio
                ? ` — ${m.portfolio.split(",")[0].replace("MLA - ", "")}`
                : ""}
            </option>
          ))}
        </select>
        {!ministerId && !isDone && (
          <p className="text-xs text-amber-600 mt-1 flex items-center gap-1">
            <AlertCircle size={10} />
            Minister must be assigned before approving
          </p>
        )}
      </div>

      {/* Statement text */}
      <div className="mb-3">
        <label className="block text-xs font-medium text-gray-600 mb-1">
          Statement
        </label>
        {isEditing ? (
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={4}
            className="w-full border border-gray-300 rounded-lg p-3
              text-sm text-gray-600 focus:outline-none focus:border-green-500"
          />
        ) : (
          <p
            className="text-gray-800 text-sm leading-relaxed bg-gray-50
            rounded-lg p-3 border border-gray-100"
          >
            {result.edited_statement_text || result.statement_text}
          </p>
        )}
      </div>

      {/* Topic */}
      <div className="mb-3">
        <label className="block text-xs font-medium text-gray-600 mb-1">
          Topic
        </label>
        <select
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          disabled={isDone && !isEditing}
          className="w-full border border-gray-300 rounded-lg px-3 py-2
            text-sm text-gray-600 focus:outline-none focus:border-green-500
            disabled:bg-gray-50"
        >
          <option value="">— No topic —</option>
          {TOPICS.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
      </div>

      {/* Context */}
      {result.context_description && (
        <div className="mb-3">
          <button
            onClick={() => setShowContext(!showContext)}
            className="flex items-center gap-1 text-xs text-gray-500
              hover:text-gray-700"
          >
            {showContext ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
            {showContext ? "Hide" : "Show"} context from article
          </button>
          {showContext && (
            <div
              className="mt-2 bg-blue-50 border border-blue-100
              rounded-lg p-3 text-xs text-blue-800 leading-relaxed"
            >
              {result.context_description}
            </div>
          )}
        </div>
      )}

      {/* Actions */}
      {!isDone && (
        <div
          className="flex items-center gap-2 pt-3
          border-t border-gray-100"
        >
          {isEditing ? (
            <>
              <button
                onClick={() => saveMutation.mutate()}
                disabled={isLoading}
                className="flex items-center gap-1.5 bg-blue-600
                  text-white px-3 py-1.5 rounded-lg text-sm
                  font-medium hover:bg-blue-700 disabled:opacity-50"
              >
                <Save size={13} />
                Save changes
              </button>
              <button
                onClick={() => {
                  setIsEditing(false);
                  setActionError("");
                }}
                className="px-3 py-1.5 rounded-lg text-sm
                  border border-gray-200 text-gray-600 hover:bg-gray-50"
              >
                Cancel
              </button>
            </>
          ) : (
            <>
              <button
                onClick={() => approveMutation.mutate()}
                disabled={isLoading || !ministerId}
                className="flex items-center gap-1.5 bg-green-700
                  text-white px-3 py-1.5 rounded-lg text-sm
                  font-medium hover:bg-green-800 disabled:opacity-50"
              >
                {approveMutation.isPending ? (
                  <Loader2 size={13} className="animate-spin" />
                ) : (
                  <CheckCircle size={13} />
                )}
                Approve
              </button>
              <button
                onClick={() => setIsEditing(true)}
                className="flex items-center gap-1.5 border
                  border-gray-300 text-gray-700 px-3 py-1.5
                  rounded-lg text-sm font-medium hover:bg-gray-50"
              >
                <Edit size={13} />
                Edit
              </button>
              <button
                onClick={() => rejectMutation.mutate()}
                disabled={isLoading}
                className="flex items-center gap-1.5 border
                  border-red-200 text-red-600 px-3 py-1.5
                  rounded-lg text-sm font-medium hover:bg-red-50
                  disabled:opacity-50"
              >
                <XCircle size={13} />
                Reject
              </button>
            </>
          )}
        </div>
      )}

      {actionError && (
        <div
          className="mt-3 rounded-lg border border-red-200
          bg-red-50 px-3 py-2 text-sm text-red-700"
        >
          {actionError}
        </div>
      )}

      {/* Approved statement link */}
      {isApproved && result.statement_id && (
        <div className="pt-3 border-t border-green-200">
          <Link
            href={`/statements/${result.statement_id}`}
            className="text-xs text-green-700 hover:underline
              flex items-center gap-1"
          >
            View published statement →
          </Link>
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────
// Add Manual Statement
// ─────────────────────────────────────────

interface AddManualStatementProps {
  itemId: number;
  ministers: Minister[];
  onAdd: () => void;
}

function AddManualStatement({
  itemId,
  ministers,
  onAdd,
}: AddManualStatementProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [ministerId, setMinisterId] = useState("");
  const [text, setText] = useState("");
  const [topic, setTopic] = useState("");
  const [context, setContext] = useState("");
  const [formError, setFormError] = useState("");

  const addMutation = useMutation({
    mutationFn: () =>
      api.addManualStatement(itemId, {
        minister_id: Number(ministerId),
        statement_text: text,
        topic: topic || null,
        context_text: context || null,
      }),
    onSuccess: () => {
      setFormError("");
      setIsOpen(false);
      setMinisterId("");
      setText("");
      setTopic("");
      setContext("");
      onAdd();
    },
    onError: (error: unknown) => {
      setFormError(
        (error as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || "Unable to add statement",
      );
    },
  });

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="mt-4 flex items-center gap-2 w-full border-2
          border-dashed border-gray-300 rounded-lg p-4 text-sm
          text-gray-500 hover:border-green-400 hover:text-green-700
          transition-colors"
      >
        <Plus size={16} />
        Add a statement the miner missed
      </button>
    );
  }

  return (
    <div
      className="mt-4 border-2 border-dashed border-green-400
      rounded-lg p-5 bg-green-50/30"
    >
      <h3
        className="font-semibold text-gray-900 text-sm mb-4 flex
        items-center gap-2"
      >
        <Plus size={14} className="text-green-700" />
        Add manual statement
      </h3>

      <div className="space-y-3">
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">
            Minister *
          </label>
          <select
            value={ministerId}
            onChange={(e) => setMinisterId(e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-3
              py-2 text-sm focus:outline-none focus:border-green-500"
          >
            <option value="">— Select minister —</option>
            {ministers.map((m) => (
              <option key={m.id} value={m.id.toString()}>
                {m.name}
                {m.portfolio
                  ? ` — ${m.portfolio.split(",")[0].replace("MLA - ", "")}`
                  : ""}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">
            Statement text *
          </label>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={3}
            placeholder="Enter the statement..."
            className="w-full border border-gray-300 rounded-lg p-3
              text-sm focus:outline-none focus:border-green-500"
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">
            Topic
          </label>
          <select
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-3
              py-2 text-sm focus:outline-none focus:border-green-500"
          >
            <option value="">— No topic —</option>
            {TOPICS.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">
            Context (optional)
          </label>
          <textarea
            value={context}
            onChange={(e) => setContext(e.target.value)}
            rows={2}
            placeholder="Surrounding context from the article..."
            className="w-full border border-gray-300 rounded-lg p-3
              text-sm focus:outline-none focus:border-green-500"
          />
        </div>

        {formError && (
          <div
            className="text-sm text-red-700 bg-red-50 rounded-lg
            p-3 mb-2 border border-red-200"
          >
            {formError}
          </div>
        )}
        <div className="flex items-center gap-2 pt-1">
          <button
            onClick={() => {
              setFormError("");
              addMutation.mutate();
            }}
            disabled={addMutation.isPending || !ministerId || !text.trim()}
            className="flex items-center gap-1.5 bg-green-700
              text-white px-4 py-2 rounded-lg text-sm font-medium
              hover:bg-green-800 disabled:opacity-50"
          >
            {addMutation.isPending ? (
              <Loader2 size={13} className="animate-spin" />
            ) : (
              <CheckCircle size={13} />
            )}
            Add & Publish
          </button>
          <button
            onClick={() => {
              setIsOpen(false);
              setFormError("");
            }}
            className="px-4 py-2 rounded-lg text-sm border
              border-gray-200 text-gray-600 hover:bg-gray-50"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
