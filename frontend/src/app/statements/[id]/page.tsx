"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import Image from "next/image";
import Link from "next/link";
import {
  ArrowLeft,
  Calendar,
  ExternalLink,
  Share2,
  User,
  CheckCircle,
  Copy,
  FileText,
} from "lucide-react";
import { useState, useEffect } from "react";
import { cn } from "@/lib/utils";

interface StatementDetail {
  id: number;
  text: string;
  topic: string | null;
  context_text: string | null;
  date: string | null;
  minister: {
    id: number;
    name: string;
    portfolio: string | null;
    party: string | null;
    constituency: string | null;
    image_url: string | null;
  };
  source: {
    publication: string | null;
    url: string | null;
    title: string | null;
    published_at: string | null;
  };
  verified_at: string | null;
  related_statements: StatementDetail[];
}

export default function StatementDetailPage() {
  const params = useParams();
  const id = Number(params.id);
  const [copied, setCopied] = useState(false);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["statement-detail", id],
    queryFn: () => api.getStatementDetail(id),
    enabled: !!id,
  });

  const statement: StatementDetail | null = data?.data || null;

  useEffect(() => {
    if (!statement) return;

    document.title = `${statement.minister.name} on ${
      statement.topic || "Kerala Politics"
    } | openMinistry`;
  }, [statement]);

  const shareUrl =
    typeof window !== "undefined"
      ? `${window.location.origin}/statements/${id}`
      : `/statements/${id}`;

  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: `Statement by ${statement?.minister?.name}`,
          text: statement?.text,
          url: shareUrl,
        });
      } catch {
        copyToClipboard();
      }
    } else {
      copyToClipboard();
    }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(shareUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (isLoading) {
    return (
      <div className="max-w-2xl mx-auto">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 rounded w-24" />
          <div className="h-32 bg-gray-200 rounded" />
          <div className="h-48 bg-gray-200 rounded" />
        </div>
      </div>
    );
  }

  if (isError || !statement) {
    return (
      <div className="max-w-2xl mx-auto text-center py-16">
        <FileText size={40} className="text-gray-300 mx-auto mb-3" />
        <p className="text-gray-600 font-medium">Statement not found</p>
        <Link
          href="/statements"
          className="text-green-700 hover:underline text-sm mt-2
            inline-block"
        >
          Browse all statements
        </Link>
      </div>
    );
  }

  const date = statement.date
    ? new Date(statement.date).toLocaleDateString("en-IN", {
        day: "numeric",
        month: "long",
        year: "numeric",
      })
    : null;

  const verifiedDate = statement.verified_at
    ? new Date(statement.verified_at).toLocaleDateString("en-IN", {
        day: "numeric",
        month: "short",
        year: "numeric",
      })
    : null;

  return (
    <div className="max-w-2xl mx-auto">
      {/* Back */}
      <Link
        href="/statements"
        className="flex items-center gap-1.5 text-sm text-gray-500
          hover:text-gray-700 mb-6"
      >
        <ArrowLeft size={14} />
        All statements
      </Link>

      {/* Main statement card */}
      <div className="border border-gray-200 rounded-xl p-6 bg-white mb-4">
        {/* Minister */}
        <Link
          href={`/ministers/${statement.minister.id}`}
          className="flex items-center gap-3 mb-5 group"
        >
          {statement.minister.image_url ? (
            <div
              className="w-12 h-12 rounded-full overflow-hidden
              border-2 border-gray-200 flex-shrink-0"
            >
              <Image
                src={statement.minister.image_url}
                alt={statement.minister.name}
                width={48}
                height={48}
                className="object-cover w-full h-full"
              />
            </div>
          ) : (
            <div
              className="w-12 h-12 rounded-full bg-green-100
              flex items-center justify-center flex-shrink-0"
            >
              <User size={20} className="text-green-700" />
            </div>
          )}
          <div>
            <p
              className="font-bold text-gray-900 group-hover:text-green-700
              transition-colors"
            >
              {statement.minister.name}
            </p>
            <p className="text-sm text-gray-500">
              {statement.minister.portfolio
                ?.split(",")[0]
                .replace("MLA - ", "") || ""}
              {statement.minister.constituency &&
                ` · ${statement.minister.constituency}`}
            </p>
          </div>
        </Link>

        {/* Topic */}
        {statement.topic && (
          <span
            className="inline-block text-xs bg-green-50
            text-green-700 px-2.5 py-1 rounded-full border
            border-green-200 mb-4 font-medium"
          >
            {statement.topic}
          </span>
        )}

        {/* Statement text */}
        <blockquote
          className="text-gray-900 text-lg leading-relaxed
          mb-5 font-medium border-l-4 border-green-500 pl-4"
        >
          {statement.text}
        </blockquote>

        {/* Context */}
        {statement.context_text && (
          <div
            className="bg-blue-50 border border-blue-100 rounded-lg
            p-4 mb-5"
          >
            <p className="text-xs font-medium text-blue-700 mb-1">
              Context from article
            </p>
            <p className="text-sm text-blue-800 leading-relaxed">
              {statement.context_text}
            </p>
          </div>
        )}

        {/* Meta */}
        <div
          className="flex items-center gap-4 text-sm text-gray-500
          mb-5 flex-wrap"
        >
          {date && (
            <span className="flex items-center gap-1.5">
              <Calendar size={13} />
              {date}
            </span>
          )}
          {statement.source.publication && (
            <span>{statement.source.publication}</span>
          )}
          {verifiedDate && (
            <span className="flex items-center gap-1 text-green-600">
              <CheckCircle size={13} />
              Verified {verifiedDate}
            </span>
          )}
        </div>

        {/* Actions */}
        <div
          className="flex items-center gap-2 pt-4
          border-t border-gray-100"
        >
          {statement.source.url && (
            <a
              href={statement.source.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 border border-gray-200
                text-gray-600 px-3 py-2 rounded-lg text-sm
                hover:bg-gray-50 transition-colors"
            >
              <ExternalLink size={14} />
              Read source article
            </a>
          )}
          <button
            onClick={handleShare}
            className={cn(
              "flex items-center gap-1.5 px-3 py-2 rounded-lg",
              "text-sm transition-colors",
              copied
                ? "bg-green-700 text-white"
                : "border border-gray-200 text-gray-600 hover:bg-gray-50",
            )}
          >
            {copied ? (
              <>
                <Copy size={14} />
                Link copied!
              </>
            ) : (
              <>
                <Share2 size={14} />
                Share
              </>
            )}
          </button>
        </div>
      </div>

      {/* Related statements */}
      {statement.related_statements.length > 0 && (
        <div>
          <h2
            className="text-sm font-semibold text-gray-700 mb-3
            flex items-center gap-2"
          >
            <FileText size={14} className="text-gray-400" />
            Other statements from this article
          </h2>
          <div className="space-y-3">
            {statement.related_statements.map((related) => (
              <RelatedStatementCard key={related.id} statement={related} />
            ))}
          </div>
        </div>
      )}

      {/* More from this minister */}
      <div className="mt-6 pt-4 border-t border-gray-200">
        <Link
          href={`/ministers/${statement.minister.id}`}
          className="flex items-center justify-between text-sm
            text-gray-600 hover:text-green-700 transition-colors"
        >
          <span>More statements by {statement.minister.name}</span>
          <span>→</span>
        </Link>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────
// Related Statement Card
// ─────────────────────────────────────────

function RelatedStatementCard({ statement }: { statement: StatementDetail }) {
  return (
    <Link href={`/statements/${statement.id}`}>
      <div
        className="border border-gray-200 rounded-lg p-4 bg-white
        hover:border-green-300 transition-colors"
      >
        <div className="flex items-center gap-2 mb-2">
          {statement.minister.image_url ? (
            <div
              className="w-6 h-6 rounded-full overflow-hidden
              border border-gray-200 flex-shrink-0"
            >
              <Image
                src={statement.minister.image_url}
                alt={statement.minister.name}
                width={24}
                height={24}
                className="object-cover w-full h-full"
              />
            </div>
          ) : (
            <div
              className="w-6 h-6 rounded-full bg-green-100
              flex items-center justify-center flex-shrink-0"
            >
              <User size={10} className="text-green-700" />
            </div>
          )}
          <span className="text-xs font-medium text-gray-700">
            {statement.minister.name}
          </span>
          {statement.topic && (
            <span
              className="text-xs bg-gray-100 text-gray-600
              px-1.5 py-0.5 rounded-full"
            >
              {statement.topic}
            </span>
          )}
        </div>
        <p className="text-sm text-gray-700 leading-relaxed line-clamp-2">
          {statement.text}
        </p>
      </div>
    </Link>
  );
}
