"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Flag, ExternalLink, CheckCircle, XCircle, Loader2 } from "lucide-react";

interface FlaggedStatement {
  id: number;
  statement_text: string;
  minister_name: string;
  minister_portfolio: string | null;
  topic: string | null;
  article_source: string | null;
  article_url: string | null;
  flag_count: number;
  flag_reason: string | null;
}

export default function FlaggedStatements() {
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["flagged-statements"],
    queryFn: () => api.getFlaggedStatements(),
    refetchInterval: 30000,
  });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["flagged-statements"] });
    queryClient.invalidateQueries({ queryKey: ["moderation-stats"] });
  };

  const dismissMutation = useMutation({
    mutationFn: (id: number) => api.dismissFlag(id),
    onSuccess: invalidate,
  });

  const rejectMutation = useMutation({
    mutationFn: (id: number) => api.rejectStatement(id, "Removed after flag"),
    onSuccess: invalidate,
  });

  const statements: FlaggedStatement[] = data?.data?.statements || [];
  const total: number = data?.data?.total || 0;

  return (
    <section className="mb-8">
      <h2 className="flex items-center gap-2 font-semibold text-foreground mb-3">
        <Flag size={18} className="text-amber-500" />
        Flagged for re-evaluation
        {total > 0 && (
          <span className="text-xs font-medium bg-amber-500/15 text-amber-600 dark:text-amber-400 px-2 py-0.5 rounded-full">
            {total}
          </span>
        )}
      </h2>

      {isLoading ? (
        <div className="rounded-xl border border-border bg-surface p-5 shadow-sm">
          <Loader2 size={18} className="animate-spin text-muted-2" />
        </div>
      ) : statements.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border bg-surface-2/50 p-5 text-sm text-muted">
          Nothing flagged right now. Statements reported by readers will appear
          here for re-evaluation.
        </div>
      ) : (
        <div className="space-y-3">
          {statements.map((s) => {
            const busy =
              (dismissMutation.isPending &&
                dismissMutation.variables === s.id) ||
              (rejectMutation.isPending && rejectMutation.variables === s.id);
            return (
              <div
                key={s.id}
                className="rounded-xl border border-amber-500/40 bg-surface p-4 shadow-sm"
              >
                <div className="flex items-start justify-between gap-3 mb-2">
                  <div>
                    <span className="font-semibold text-foreground text-sm">
                      {s.minister_name}
                    </span>
                    {s.minister_portfolio && (
                      <span className="ml-2 text-xs text-muted">
                        {s.minister_portfolio.split(",")[0].replace("MLA - ", "")}
                      </span>
                    )}
                  </div>
                  <span className="shrink-0 flex items-center gap-1 text-xs font-medium text-amber-600 dark:text-amber-400 bg-amber-500/15 px-2 py-1 rounded-full">
                    <Flag size={11} />
                    {s.flag_count} flag{s.flag_count !== 1 ? "s" : ""}
                  </span>
                </div>

                <p className="text-sm text-foreground/90 leading-relaxed mb-2">
                  {s.statement_text}
                </p>

                {s.flag_reason && (
                  <p className="text-xs text-muted mb-2">
                    <span className="font-medium text-foreground">
                      Reader note:
                    </span>{" "}
                    {s.flag_reason}
                  </p>
                )}

                <div className="flex items-center gap-3 text-xs text-muted mb-3">
                  {s.article_source && <span>{s.article_source}</span>}
                  {s.article_url && (
                    <a
                      href={s.article_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1 text-accent hover:underline"
                    >
                      Source <ExternalLink size={10} />
                    </a>
                  )}
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => dismissMutation.mutate(s.id)}
                    disabled={busy}
                    className="flex items-center gap-1.5 bg-accent text-accent-contrast
                      px-3 py-1.5 rounded-lg text-sm font-medium
                      hover:bg-accent-hover disabled:opacity-50"
                  >
                    <CheckCircle size={14} />
                    Keep (dismiss flag)
                  </button>
                  <button
                    onClick={() => {
                      if (
                        window.confirm(
                          "Remove this statement from the public site?",
                        )
                      ) {
                        rejectMutation.mutate(s.id);
                      }
                    }}
                    disabled={busy}
                    className="flex items-center gap-1.5 border border-danger-border
                      text-danger px-3 py-1.5 rounded-lg text-sm font-medium
                      hover:bg-danger/10 disabled:opacity-50"
                  >
                    <XCircle size={14} />
                    Remove
                  </button>
                  {busy && (
                    <Loader2 size={14} className="animate-spin text-muted-2" />
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}
