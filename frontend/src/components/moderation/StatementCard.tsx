"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import {
  CheckCircle, XCircle, Edit, Flag,
  ExternalLink, ChevronDown, ChevronUp,
} from "lucide-react";
import { cn } from "@/lib/utils";

export interface StatementCardProps {
  statement: {
    id: number;
    statement_text: string;
    confidence_score: number;
    minister_name: string;
    minister_id: number;
    minister_portfolio: string;
    article_title: string;
    article_url: string;
    article_source: string;
    article_published_at: string;
    statement_date: string;
    topic: string | null;
  };
}

export default function StatementCard({ statement }: StatementCardProps) {
  const queryClient = useQueryClient();
  const [showEdit, setShowEdit] = useState(false);
  const [editedText, setEditedText] = useState(statement.statement_text);
  const [editedTopic, setEditedTopic] = useState(statement.topic || "");
  const [notes, setNotes] = useState("");
  const [showContext, setShowContext] = useState(false);
  const [context, setContext] = useState<string | null>(null);

  const TOPICS = [
    "Health", "Education", "Transport", "Economy",
    "Agriculture", "Environment", "Infrastructure",
    "Law & Order", "Social Welfare", "Politics",
    "Tourism", "Finance", "Sport",
  ];

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["moderation-queue"] });
    queryClient.invalidateQueries({ queryKey: ["moderation-stats"] });
  };

  const approveMutation = useMutation({
    mutationFn: () => api.approveStatement(statement.id, notes || undefined),
    onSuccess: invalidate,
  });

  const rejectMutation = useMutation({
    mutationFn: () => api.rejectStatement(statement.id, notes || undefined),
    onSuccess: invalidate,
  });

  const editMutation = useMutation({
    mutationFn: () =>
      api.reviewStatement(statement.id, {
        action: "edited",
        edited_text: editedText,
        notes: notes || undefined,
      }),
    onSuccess: async () => {
      // Also update topic if changed
      if (editedTopic !== (statement.topic || "")) {
        await api.updateStatement(statement.id, { topic: editedTopic });
      }
      invalidate();
      setShowEdit(false);
    },
  });

  const flagMutation = useMutation({
    mutationFn: () =>
      api.reviewStatement(statement.id, {
        action: "needs_review",
        notes: notes || undefined,
      }),
    onSuccess: invalidate,
  });

  const loadContext = async () => {
    if (context) {
      setShowContext(!showContext);
      return;
    }
    try {
      const res = await api.getStatementContext(statement.id);
      setContext(res.data.article_content || "No content available");
      setShowContext(true);
    } catch {
      setContext("Could not load article content");
      setShowContext(true);
    }
  };

  const confidence = statement.confidence_score || 0;
  const confidenceColor =
    confidence >= 0.8
      ? "text-accent bg-accent-soft"
      : confidence >= 0.6
      ? "text-amber-600 dark:text-amber-400 bg-amber-500/10"
      : "text-red-600 dark:text-red-400 bg-red-500/10";

  const isLoading =
    approveMutation.isPending ||
    rejectMutation.isPending ||
    editMutation.isPending ||
    flagMutation.isPending;

  return (
    <div className="border border-border rounded-xl p-5 bg-surface shadow-sm">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <span className="font-semibold text-foreground">
            {statement.minister_name}
          </span>
          {statement.minister_portfolio && (
            <span className="ml-2 text-sm text-muted">
              {statement.minister_portfolio.split(",")[0].replace("MLA - ", "")}
            </span>
          )}
        </div>
        <span
          className={cn(
            "text-xs font-medium px-2 py-1 rounded-full",
            confidenceColor,
          )}
        >
          {Math.round(confidence * 100)}% confidence
        </span>
      </div>

      {/* Statement text */}
      {showEdit ? (
        <div className="space-y-3 mb-3">
          {/* Edit text */}
          <div>
            <label className="block text-xs font-medium text-muted mb-1">
              Statement text
            </label>
            <textarea
              value={editedText}
              onChange={(e) => setEditedText(e.target.value)}
              className="w-full border border-border bg-surface text-foreground rounded-lg p-3
                text-sm focus:outline-none
                focus:border-accent focus:ring-1 focus:ring-accent"
              rows={4}
            />
          </div>

          {/* Edit topic */}
          <div>
            <label className="block text-xs font-medium text-muted mb-1">
              Topic
            </label>
            <select
              value={editedTopic}
              onChange={(e) => setEditedTopic(e.target.value)}
              className="w-full border border-border bg-surface text-foreground rounded-lg px-3
                py-2 text-sm focus:outline-none focus:border-accent"
            >
              <option value="">No topic</option>
              {TOPICS.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>

          {/* Notes */}
          <div>
            <label className="block text-xs font-medium text-muted mb-1">
              Edit notes
            </label>
            <input
              type="text"
              placeholder="Reason for edit..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="w-full border border-border bg-surface text-foreground rounded-lg px-3
                py-2 text-xs focus:outline-none
                focus:border-accent"
            />
          </div>
        </div>
      ) : (
        <p className="text-foreground/90 text-sm leading-relaxed mb-3">
          {statement.statement_text}
        </p>
      )}

      {/* Topic badge */}
      {!showEdit && statement.topic && (
        <span
          className="inline-block text-xs bg-accent-soft text-accent-soft-fg
          px-2 py-0.5 rounded-full border border-accent-border mb-3"
        >
          {statement.topic}
        </span>
      )}

      {/* Source */}
      <div className="flex items-center gap-3 mb-3 text-xs text-muted">
        <span>{statement.article_source || "Unknown source"}</span>
        <span>•</span>
        <span>
          {statement.article_published_at
            ? new Date(statement.article_published_at).toLocaleDateString(
                "en-IN",
              )
            : "Unknown date"}
        </span>
        {statement.article_url && (
          <>
            <span>•</span>
            <a
              href={statement.article_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 text-accent hover:underline"
            >
              Source <ExternalLink size={10} />
            </a>
          </>
        )}
      </div>

      {/* Article context toggle */}
      <button
        onClick={loadContext}
        className="flex items-center gap-1 text-xs text-muted
          hover:text-foreground mb-3"
      >
        {showContext ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        {showContext ? "Hide" : "Show"} original article
      </button>

      {showContext && context && (
        <div
          className="bg-surface-2 rounded-lg p-3 mb-3 text-xs
          text-muted max-h-48 overflow-y-auto leading-relaxed
          border border-border"
        >
          {context}
        </div>
      )}

      {/* Notes field for approve/reject */}
      {!showEdit && (
        <input
          type="text"
          placeholder="Optional notes..."
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          className="w-full border border-border bg-surface text-foreground rounded-lg px-3 py-2
            text-xs focus:outline-none
            focus:border-accent mb-3"
        />
      )}

      {/* Action buttons */}
      <div className="flex items-center gap-2 flex-wrap">
        {showEdit ? (
          <>
            <button
              onClick={() => editMutation.mutate()}
              disabled={isLoading || editedText.length < 10}
              className="flex items-center gap-1.5 bg-accent
                text-accent-contrast px-3 py-1.5 rounded-lg text-sm font-medium
                hover:bg-accent-hover disabled:opacity-50"
            >
              <CheckCircle size={14} />
              Save & Approve
            </button>
            <button
              onClick={() => {
                setShowEdit(false);
                setEditedText(statement.statement_text);
                setEditedTopic(statement.topic || "");
                setNotes("");
              }}
              className="px-3 py-1.5 rounded-lg text-sm text-muted
                border border-border hover:bg-surface-2 hover:text-foreground"
            >
              Cancel
            </button>
          </>
        ) : (
          <>
            <button
              onClick={() => approveMutation.mutate()}
              disabled={isLoading}
              className="flex items-center gap-1.5 bg-accent
                text-accent-contrast px-3 py-1.5 rounded-lg text-sm font-medium
                hover:bg-accent-hover disabled:opacity-50"
            >
              <CheckCircle size={14} />
              Approve
            </button>
            <button
              onClick={() => rejectMutation.mutate()}
              disabled={isLoading}
              className="flex items-center gap-1.5 bg-red-600
                text-white px-3 py-1.5 rounded-lg text-sm font-medium
                hover:bg-red-700 disabled:opacity-50"
            >
              <XCircle size={14} />
              Reject
            </button>
            <button
              onClick={() => setShowEdit(true)}
              disabled={isLoading}
              className="flex items-center gap-1.5 border border-border
                text-foreground px-3 py-1.5 rounded-lg text-sm font-medium
                hover:bg-surface-2 disabled:opacity-50"
            >
              <Edit size={14} />
              Edit
            </button>
            <button
              onClick={() => flagMutation.mutate()}
              disabled={isLoading}
              className="flex items-center gap-1.5 border border-amber-500/40
                text-amber-600 dark:text-amber-400 px-3 py-1.5 rounded-lg text-sm font-medium
                hover:bg-amber-500/10 disabled:opacity-50"
            >
              <Flag size={14} />
              Flag
            </button>
          </>
        )}
      </div>
    </div>
  );
}