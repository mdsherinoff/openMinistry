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
            className="border border-gray-200 rounded-lg p-4 animate-pulse"
          >
            <div className="h-4 bg-gray-200 rounded mb-2 w-20" />
            <div className="h-8 bg-gray-200 rounded w-12" />
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
      color: "text-amber-600",
      bg: "bg-amber-50",
    },
    {
      label: "Approved",
      value: stats.approved,
      icon: CheckCircle,
      color: "text-green-600",
      bg: "bg-green-50",
    },
    {
      label: "Rejected",
      value: stats.rejected,
      icon: XCircle,
      color: "text-red-600",
      bg: "bg-red-50",
    },
    {
      label: "Needs Review",
      value: stats.needs_review,
      icon: AlertCircle,
      color: "text-blue-600",
      bg: "bg-blue-50",
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      {cards.map(({ label, value, icon: Icon, color, bg }) => (
        <div key={label} className="border border-gray-200 rounded-lg p-4">
          <div className={`inline-flex p-2 rounded-lg ${bg} mb-2`}>
            <Icon size={18} className={color} />
          </div>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          <p className="text-sm text-gray-500">{label}</p>
        </div>
      ))}
    </div>
  );
}
