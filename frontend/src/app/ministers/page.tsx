"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import Link from "next/link";
import { Users, Search, Building } from "lucide-react";
import { MinisterCardSkeleton } from "@/components/ui/Skeleton";
import Image from "next/image";

interface Minister {
  id: number;
  name: string;
  name_malayalam: string | null;
  portfolio: string | null;
  party: string | null;
  constituency: string | null;
  is_active: number;
  bio: string | null;
  image_url: string | null;
}

export default function MinistersPage() {
  const [activeParty, setActiveParty] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["ministers"],
    queryFn: () => api.getMinisters(true),
  });

  const ministers: Minister[] = data?.data || [];

  const partyCounts = ministers.reduce((acc: Record<string, number>, m) => {
    const party = m.party?.trim() || "Unknown";
    acc[party] = (acc[party] || 0) + 1;
    return acc;
  }, {});

  const top5Parties = Object.entries(partyCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .map(([party]) => party);

  const allParties = Object.keys(partyCounts);
  const otherParties = allParties.filter((p) => !top5Parties.includes(p));

  const filtered = ministers.filter((m) => {
    const s = search.toLowerCase();
    const matchesSearch =
      !search ||
      m.name.toLowerCase().includes(s) ||
      m.portfolio?.toLowerCase().includes(s) ||
      m.constituency?.toLowerCase().includes(s) ||
      m.party?.toLowerCase().includes(s);

    const matchesParty =
      !activeParty ||
      (activeParty === "Others"
        ? m.party && otherParties.includes(m.party)
        : m.party === activeParty);

    return matchesSearch && matchesParty;
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
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Ministers & MLAs
          </h1>
        </div>
        <p className="text-gray-500 dark:text-gray-400">
          16th Kerala Legislative Assembly — {ministers.length} members
        </p>
      </div>

      {/* Party Filters */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
        {top5Parties.map((party) => (
          <button
            key={party}
            onClick={() => setActiveParty(activeParty === party ? null : party)}
            className={`p-3 rounded-lg border text-xs font-medium transition-colors ${
              activeParty === party
                ? "bg-green-600 text-white border-green-600"
                : "bg-white dark:bg-gray-900 hover:border-green-300 border-gray-200 dark:border-gray-700 text-gray-900 dark:text-gray-100"
            }`}
          >
            {party}
            <div className="text-[10px] opacity-70">
              {partyCounts[party]} members
            </div>
          </button>
        ))}

        <button
          onClick={() =>
            setActiveParty(activeParty === "Others" ? null : "Others")
          }
          className={`p-3 rounded-lg border text-xs font-medium transition-colors ${
            activeParty === "Others"
              ? "bg-green-600 text-white border-green-600"
              : "bg-white dark:bg-gray-900 hover:border-green-300 border-gray-200 dark:border-gray-700 text-gray-900 dark:text-gray-100"
          }`}
        >
          Others
          <div className="text-[10px] opacity-70">
            {otherParties.reduce((sum, p) => sum + (partyCounts[p] || 0), 0)}{" "}
            members
          </div>
        </button>
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
          className="w-full pl-9 pr-4 py-2.5 border border-gray-300 dark:border-gray-700
            rounded-lg text-sm bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100
            placeholder-gray-400 dark:placeholder-gray-500
            focus:outline-none focus:border-green-500 focus:ring-1 focus:ring-green-500"
        />
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(9)].map((_, i) => (
            <MinisterCardSkeleton key={i} />
          ))}
        </div>
      ) : (
        <>
          {/* Cabinet Ministers */}
          {cabinetMinisters.length > 0 && (
            <div className="mb-8">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <Building size={18} className="text-green-700" />
                Council of Ministers
                <span className="text-sm font-normal text-gray-500 dark:text-gray-400">
                  ({cabinetMinisters.length})
                </span>
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {cabinetMinisters.map((minister) => (
                  <MinisterCard key={minister.id} minister={minister} />
                ))}
              </div>
            </div>
          )}

          {/* MLAs */}
          {mlas.length > 0 && (
            <div>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <Users size={18} className="text-green-700" />
                Members of Legislative Assembly
                <span className="text-sm font-normal text-gray-500 dark:text-gray-400">
                  ({mlas.length})
                </span>
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {mlas.map((minister) => (
                  <MinisterCard key={minister.id} minister={minister} />
                ))}
              </div>
            </div>
          )}

          {filtered.length === 0 && (
            <div className="text-center py-16 text-gray-500 dark:text-gray-400">
              No members found matching &ldquo;{search}&rdquo;
            </div>
          )}
        </>
      )}
    </div>
  );
}

function MinisterCard({ minister }: { minister: Minister }) {
  const isMinister = minister.portfolio?.toLowerCase().includes("minister");

  const displayPortfolio = minister.portfolio
    ?.replace("MLA - ", "")
    .split(",")[0]
    .trim();

  return (
    <Link href={`/ministers/${minister.id}`}>
      <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 bg-white dark:bg-gray-900 hover:border-green-300 dark:hover:border-green-700 hover:shadow-sm transition-all cursor-pointer">
        <div className="flex items-start justify-between mb-2">
          {minister.image_url ? (
            <div className="w-10 h-10 rounded-full overflow-hidden border border-gray-200 dark:border-gray-700 flex-shrink-0">
              <Image
                src={minister.image_url}
                alt={minister.name}
                width={40}
                height={40}
                className="object-cover w-full h-full"
              />
            </div>
          ) : (
            <div className="w-10 h-10 rounded-full bg-green-100 dark:bg-green-900 flex items-center justify-center text-green-700 dark:text-green-400 font-semibold text-sm flex-shrink-0">
              {minister.name.charAt(0)}
            </div>
          )}

          {isMinister && (
            <span className="text-xs bg-green-50 dark:bg-green-900/40 text-green-700 dark:text-green-400 px-2 py-0.5 rounded-full border border-green-200 dark:border-green-800">
              Minister
            </span>
          )}
        </div>

        <p className="font-semibold text-gray-900 dark:text-gray-100 text-sm mb-1">
          {minister.name}
        </p>
        {minister.name_malayalam && (
          <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">
            {minister.name_malayalam}
          </p>
        )}
        {displayPortfolio && (
          <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">
            {displayPortfolio}
          </p>
        )}
        {minister.constituency && (
          <p className="text-xs text-gray-400 dark:text-gray-500">
            {minister.party}
          </p>
        )}
      </div>
    </Link>
  );
}
