"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { getPartyFlagUrl } from "@/lib/partyFlags";
import StatementCard from "@/components/StatementCard";
import Link from "next/link";
import Image from "next/image";
import {
  ArrowLeft,
  User,
  MapPin,
  Building,
  FileText,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";

export default function MinisterPage() {
  const params = useParams();
  const id = Number(params.id);
  const [offset, setOffset] = useState(0);
  const limit = 10;

  const { data, isLoading } = useQuery({
    queryKey: ["minister-statements", id, offset],
    queryFn: () =>
      api.getMinisterStatements(id, {
        limit: String(limit),
        offset: String(offset),
      }),
    enabled: !!id,
  });

  const { data: statsData } = useQuery({
    queryKey: ["minister-stats", id],
    queryFn: () => api.getMinisterStats(id),
    enabled: !!id,
  });

  const ministerData = data?.data;
  const minister = ministerData?.minister;
  const statements = ministerData?.statements || [];
  const total = ministerData?.total || 0;
  const stats = statsData?.data;

  // partyFlagUrl kept for future use
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const partyFlagUrl = minister ? getPartyFlagUrl(minister.party) : null;

  if (isLoading) {
    return (
      <div className="animate-pulse">
        <div className="h-8 bg-gray-200 dark:bg-gray-800 rounded w-48 mb-4" />
        <div className="h-32 bg-gray-200 dark:bg-gray-800 rounded mb-6" />
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <div
              key={i}
              className="h-32 bg-gray-200 dark:bg-gray-800 rounded"
            />
          ))}
        </div>
      </div>
    );
  }

  if (!minister) {
    return (
      <div className="text-center py-16">
        <p className="text-gray-600 dark:text-gray-400">Minister not found.</p>
        <Link
          href="/ministers"
          className="text-green-700 dark:text-green-400 hover:underline text-sm mt-2 inline-block"
        >
          Back to ministers
        </Link>
      </div>
    );
  }

  const isMinister = minister.portfolio?.toLowerCase().includes("minister");
  const cleanBio = minister.bio?.split("ALIASES:")[0].trim();

  return (
    <div>
      {/* Back */}
      <Link
        href="/ministers"
        className="flex items-center gap-1.5 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 mb-6 transition-colors"
      >
        <ArrowLeft size={14} />
        All Ministers & MLAs
      </Link>

      {/* Profile header */}
      <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-6 mb-6 bg-white dark:bg-gray-900">
        <div className="flex items-start gap-4">
          {minister.image_url ? (
            <div className="w-16 h-16 rounded-full overflow-hidden border-2 border-gray-200 dark:border-gray-700 flex-shrink-0">
              <Image
                src={minister.image_url}
                alt={minister.name}
                width={64}
                height={64}
                className="object-cover w-full h-full"
              />
            </div>
          ) : (
            <div className="w-16 h-16 rounded-full bg-green-100 dark:bg-green-900 flex items-center justify-center text-green-700 dark:text-green-400 font-bold text-2xl flex-shrink-0">
              {minister.name.charAt(0)}
            </div>
          )}

          <div className="flex-1">
            <div className="flex items-start justify-between">
              <div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                  {minister.name}
                </h1>
                {minister.name_malayalam && (
                  <p className="text-gray-500 dark:text-gray-400 mt-0.5">
                    {minister.name_malayalam}
                  </p>
                )}
              </div>
              {isMinister && (
                <span className="bg-green-50 dark:bg-green-900/40 text-green-700 dark:text-green-400 text-sm px-3 py-1 rounded-full border border-green-200 dark:border-green-800">
                  Minister
                </span>
              )}
            </div>

            <div className="mt-3 flex flex-wrap gap-4 text-sm text-gray-600 dark:text-gray-400">
              {minister.portfolio && (
                <span className="flex items-center gap-1.5">
                  <Building
                    size={14}
                    className="text-gray-400 dark:text-gray-500"
                  />
                  {minister.portfolio
                    .replace("MLA - ", "")
                    .split(",")[0]
                    .trim()}
                </span>
              )}
              {minister.constituency && (
                <span className="flex items-center gap-1.5">
                  <MapPin
                    size={14}
                    className="text-gray-400 dark:text-gray-500"
                  />
                  {minister.constituency}
                </span>
              )}
              {minister.party && (
                <span className="flex items-center gap-1.5">
                  <User
                    size={14}
                    className="text-gray-400 dark:text-gray-500"
                  />
                  {minister.party}
                </span>
              )}
            </div>

            {cleanBio && !cleanBio.startsWith("MLA") && (
              <p className="mt-3 text-sm text-gray-600 dark:text-gray-400">
                {cleanBio}
              </p>
            )}
          </div>
        </div>

        {/* Stats */}
        {stats && (
          <div className="mt-4 pt-4 border-t border-gray-100 dark:border-gray-800 flex items-center gap-6">
            <div className="text-center">
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {stats.total_statements}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Verified Statements
              </p>
            </div>
            {stats.topics.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {stats.topics.map((t: { topic: string; count: number }) => (
                  <span
                    key={t.topic}
                    className="text-xs bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 px-2 py-1 rounded-full"
                  >
                    {t.topic} ({t.count})
                  </span>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Statements */}
      <div>
        <div className="flex items-center gap-2 mb-4">
          <FileText size={18} className="text-green-700" />
          <h2 className="font-semibold text-gray-900 dark:text-white">
            Statements
            {total > 0 && (
              <span className="ml-2 text-sm font-normal text-gray-500 dark:text-gray-400">
                ({total} verified)
              </span>
            )}
          </h2>
        </div>

        {statements.length === 0 ? (
          <div className="text-center py-16 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-900">
            <FileText
              size={40}
              className="text-gray-300 dark:text-gray-600 mx-auto mb-3"
            />
            <p className="text-gray-600 dark:text-gray-400 font-medium">
              No verified statements yet
            </p>
            <p className="text-gray-500 dark:text-gray-500 text-sm mt-1">
              Statements are being reviewed by moderators.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {statements.map((stmt: Record<string, unknown>) => (
              <StatementCard
                key={stmt.id as number}
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                statement={stmt as any}
              />
            ))}
          </div>
        )}

        {/* Pagination */}
        {total > limit && (
          <div className="flex items-center justify-between mt-8 pt-4 border-t border-gray-200 dark:border-gray-800">
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Showing {offset + 1}–{Math.min(offset + limit, total)} of {total}
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => setOffset(Math.max(0, offset - limit))}
                disabled={offset === 0}
                className="flex items-center gap-1 px-3 py-1.5 text-sm
                  border border-gray-200 dark:border-gray-700 rounded-lg
                  disabled:opacity-50 hover:bg-gray-50 dark:hover:bg-gray-800
                  text-gray-700 dark:text-gray-300 transition-colors"
              >
                <ChevronLeft size={14} />
                Previous
              </button>
              <button
                onClick={() => setOffset(offset + limit)}
                disabled={offset + limit >= total}
                className="flex items-center gap-1 px-3 py-1.5 text-sm
                  border border-gray-200 dark:border-gray-700 rounded-lg
                  disabled:opacity-50 hover:bg-gray-50 dark:hover:bg-gray-800
                  text-gray-700 dark:text-gray-300 transition-colors"
              >
                Next
                <ChevronRight size={14} />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
