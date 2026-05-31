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
    "Tourism", "Finance",
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
      ? "text-green-600 bg-green-50"
      : confidence >= 0.6
      ? "text-amber-600 bg-amber-50"
      : "text-red-600 bg-red-50";

  const isLoading =
    approveMutation.isPending ||
    rejectMutation.isPending ||
    editMutation.isPending ||
    flagMutation.isPending;

  return (
    <div className="border border-gray-200 rounded-lg p-5 bg-white">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <span className="font-semibold text-gray-900">
            {statement.minister_name}
          </span>
          {statement.minister_portfolio && (
            <span className="ml-2 text-sm text-gray-500">
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
            <label className="block text-xs font-medium text-gray-600 mb-1">
              Statement text
            </label>
            <textarea
              value={editedText}
              onChange={(e) => setEditedText(e.target.value)}
              className="w-full border border-gray-300 rounded-lg p-3
                text-sm text-gray-800 focus:outline-none
                focus:border-green-500 focus:ring-1 focus:ring-green-500"
              rows={4}
            />
          </div>

          {/* Edit topic */}
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              Topic
            </label>
            <select
              value={editedTopic}
              onChange={(e) => setEditedTopic(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3
                py-2 text-sm focus:outline-none focus:border-green-500"
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
            <label className="block text-xs font-medium text-gray-600 mb-1">
              Edit notes
            </label>
            <input
              type="text"
              placeholder="Reason for edit..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="w-full border border-gray-200 rounded-lg px-3
                py-2 text-xs text-gray-700 focus:outline-none
                focus:border-green-500"
            />
          </div>
        </div>
      ) : (
        <p className="text-gray-800 text-sm leading-relaxed mb-3">
          {statement.statement_text}
        </p>
      )}

      {/* Topic badge */}
      {!showEdit && statement.topic && (
        <span
          className="inline-block text-xs bg-blue-50 text-blue-700
          px-2 py-0.5 rounded-full border border-blue-200 mb-3"
        >
          {statement.topic}
        </span>
      )}

      {/* Source */}
      <div className="flex items-center gap-3 mb-3 text-xs text-gray-500">
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
              className="flex items-center gap-1 text-green-700 hover:underline"
            >
              Source <ExternalLink size={10} />
            </a>
          </>
        )}
      </div>

      {/* Article context toggle */}
      <button
        onClick={loadContext}
        className="flex items-center gap-1 text-xs text-gray-500
          hover:text-gray-700 mb-3"
      >
        {showContext ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        {showContext ? "Hide" : "Show"} original article
      </button>

      {showContext && context && (
        <div
          className="bg-gray-50 rounded-lg p-3 mb-3 text-xs
          text-gray-600 max-h-48 overflow-y-auto leading-relaxed
          border border-gray-200"
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
          className="w-full border border-gray-200 rounded-lg px-3 py-2
            text-xs text-gray-700 focus:outline-none
            focus:border-green-500 mb-3"
        />
      )}

      {/* Action buttons */}
      <div className="flex items-center gap-2 flex-wrap">
        {showEdit ? (
          <>
            <button
              onClick={() => editMutation.mutate()}
              disabled={isLoading || editedText.length < 10}
              className="flex items-center gap-1.5 bg-green-700
                text-white px-3 py-1.5 rounded-lg text-sm font-medium
                hover:bg-green-800 disabled:opacity-50"
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
              className="px-3 py-1.5 rounded-lg text-sm text-gray-600
                border border-gray-200 hover:bg-gray-50"
            >
              Cancel
            </button>
          </>
        ) : (
          <>
            <button
              onClick={() => approveMutation.mutate()}
              disabled={isLoading}
              className="flex items-center gap-1.5 bg-green-700
                text-white px-3 py-1.5 rounded-lg text-sm font-medium
                hover:bg-green-800 disabled:opacity-50"
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
              className="flex items-center gap-1.5 border border-gray-300
                text-gray-700 px-3 py-1.5 rounded-lg text-sm font-medium
                hover:bg-gray-50 disabled:opacity-50"
            >
              <Edit size={14} />
              Edit
            </button>
            <button
              onClick={() => flagMutation.mutate()}
              disabled={isLoading}
              className="flex items-center gap-1.5 border border-amber-300
                text-amber-700 px-3 py-1.5 rounded-lg text-sm font-medium
                hover:bg-amber-50 disabled:opacity-50"
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