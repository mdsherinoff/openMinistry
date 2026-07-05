"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { CheckCircle, Clock, XCircle, AlertCircle } from "lucide-react";

export default function StatsCards() {
  const { data, isLoading } = useQuery({
    queryKey: ["moderation-stats"],
    queryFn: () => api.getModerationStats(),
    refetchInterval: 30000,
  });

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {[...Array(4)].map((_, i) => (
          <div
            key={i}
            className="border border-border bg-surface rounded-xl p-4 shadow-sm animate-pulse"
          >
            <div className="h-4 bg-surface-2 rounded mb-2 w-20" />
            <div className="h-8 bg-surface-2 rounded w-12" />
          </div>
        ))}
      </div>
    );
  }

  const stats = data?.data?.totals;
  if (!stats) return null;

  const cards = [
    {
      label: "Pending Review",
      value: stats.pending,
      icon: Clock,
      color: "text-amber-600 dark:text-amber-400",
      bg: "bg-amber-500/10",
    },
    {
      label: "Approved",
      value: stats.approved,
      icon: CheckCircle,
      color: "text-accent",
      bg: "bg-accent-soft",
    },
    {
      label: "Rejected",
      value: stats.rejected,
      icon: XCircle,
      color: "text-red-600 dark:text-red-400",
      bg: "bg-red-500/10",
    },
    {
      label: "Needs Review",
      value: stats.needs_review,
      icon: AlertCircle,
      color: "text-blue-600 dark:text-blue-400",
      bg: "bg-blue-500/10",
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      {cards.map(({ label, value, icon: Icon, color, bg }) => (
        <div
          key={label}
          className="border border-border bg-surface rounded-xl p-4 shadow-sm"
        >
          <div className={`inline-flex p-2 rounded-lg ${bg} mb-2`}>
            <Icon size={18} className={color} />
          </div>
          <p className="text-2xl font-bold text-foreground">{value}</p>
          <p className="text-sm text-muted">{label}</p>
        </div>
      ))}
    </div>
  );
}
