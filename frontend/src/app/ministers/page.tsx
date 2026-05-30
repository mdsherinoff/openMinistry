"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import Link from "next/link";
import { Users, Search, Building } from "lucide-react";

interface Minister {
  id: number;
  name: string;
  name_malayalam: string | null;
  portfolio: string | null;
  party: string | null;
  constituency: string | null;
  is_active: number;
  bio: string | null;
}

export default function MinistersPage() {
  const [search, setSearch] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["ministers"],
    queryFn: () => api.getMinisters(true),
  });

  const ministers: Minister[] = data?.data || [];

  const filtered = ministers.filter((m) => {
    if (!search) return true;
    const s = search.toLowerCase();
    return (
      m.name.toLowerCase().includes(s) ||
      m.portfolio?.toLowerCase().includes(s) ||
      m.constituency?.toLowerCase().includes(s) ||
      m.party?.toLowerCase().includes(s)
    );
  });

  // Separate ministers from MLAs
  const cabinetMinisters = filtered.filter(
    (m) =>
      m.portfolio &&
      !m.portfolio.startsWith("MLA") &&
      !m.bio?.startsWith("MLA"),
  );
  const mlas = filtered.filter(
    (m) => m.portfolio?.startsWith("MLA") || m.bio?.startsWith("MLA"),
  );

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-2 mb-2">
          <Users size={20} className="text-green-700" />
          <h1 className="text-2xl font-bold text-gray-900">Ministers & MLAs</h1>
        </div>
        <p className="text-gray-600">
          16th Kerala Legislative Assembly — {ministers.length} members
        </p>
      </div>

      {/* Search */}
      <div className="relative mb-6">
        <Search
          size={16}
          className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
        />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by name, portfolio, constituency..."
          className="w-full pl-9 pr-4 py-2.5 border border-gray-300
            rounded-lg text-sm focus:outline-none focus:border-green-500
            focus:ring-1 focus:ring-green-500"
        />
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <div
              key={i}
              className="border border-gray-200 rounded-lg p-4 animate-pulse"
            >
              <div className="h-4 bg-gray-200 rounded w-32 mb-2" />
              <div className="h-3 bg-gray-200 rounded w-24" />
            </div>
          ))}
        </div>
      ) : (
        <>
          {/* Cabinet Ministers */}
          {cabinetMinisters.length > 0 && (
            <div className="mb-8">
              <h2
                className="text-lg font-semibold text-gray-900 mb-4
                flex items-center gap-2"
              >
                <Building size={18} className="text-green-700" />
                Council of Ministers
                <span className="text-sm font-normal text-gray-500">
                  ({cabinetMinisters.length})
                </span>
              </h2>
              <div
                className="grid grid-cols-1 md:grid-cols-2
                lg:grid-cols-3 gap-4"
              >
                {cabinetMinisters.map((minister) => (
                  <MinisterCard key={minister.id} minister={minister} />
                ))}
              </div>
            </div>
          )}

          {/* MLAs */}
          {mlas.length > 0 && (
            <div>
              <h2
                className="text-lg font-semibold text-gray-900 mb-4
                flex items-center gap-2"
              >
                <Users size={18} className="text-green-700" />
                Members of Legislative Assembly
                <span className="text-sm font-normal text-gray-500">
                  ({mlas.length})
                </span>
              </h2>
              <div
                className="grid grid-cols-1 md:grid-cols-2
                lg:grid-cols-3 gap-4"
              >
                {mlas.map((minister) => (
                  <MinisterCard key={minister.id} minister={minister} />
                ))}
              </div>
            </div>
          )}

          {filtered.length === 0 && (
            <div className="text-center py-16 text-gray-500">
              No members found matching &ldquo;{search}&rdquo;
            </div>
          )}
        </>
      )}
    </div>
  );
}

function MinisterCard({ minister }: { minister: Minister }) {
  const isMinister =
    minister.portfolio &&
    !minister.portfolio.startsWith("MLA") &&
    minister.portfolio !== "";

  const displayPortfolio = minister.portfolio
    ?.replace("MLA - ", "")
    .split(",")[0]
    .trim();

  return (
    <Link href={`/ministers/${minister.id}`}>
      <div
        className="border border-gray-200 rounded-lg p-4 bg-white
        hover:border-green-300 hover:shadow-sm transition-all cursor-pointer"
      >
        <div className="flex items-start justify-between mb-2">
          <div
            className="w-9 h-9 rounded-full bg-green-100
            flex items-center justify-center text-green-700
            font-semibold text-sm flex-shrink-0"
          >
            {minister.name.charAt(0)}
          </div>
          {isMinister && (
            <span
              className="text-xs bg-green-50 text-green-700
              px-2 py-0.5 rounded-full border border-green-200"
            >
              Minister
            </span>
          )}
        </div>
        <p className="font-semibold text-gray-900 text-sm mb-1">
          {minister.name}
        </p>
        {minister.name_malayalam && (
          <p className="text-xs text-gray-500 mb-1">
            {minister.name_malayalam}
          </p>
        )}
        {displayPortfolio && (
          <p className="text-xs text-gray-600 mb-1">{displayPortfolio}</p>
        )}
        {minister.constituency && (
          <p className="text-xs text-gray-400">
            {minister.constituency
              .replace(/\s*\(ST\)\s*/i, " (ST)")
              .replace(/\s*\(SC\)\s*/i, " (SC)")}
          </p>
        )}
      </div>
    </Link>
  );
}
