import { ExternalLink, Calendar, User } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { Share2, Copy } from "lucide-react";
import { cn } from "@/lib/utils";
import { useState } from "react";

interface Statement {
  id: number;
  statement_text: string;
  statement_date: string | null;
  context_text?: string | null;
  topic: string | null;
  confidence_score: number;
  minister: {
    id: number;
    name: string;
    portfolio: string | null;
    image_url?: string | null;
  };
  source: {
    name: string | null;
    url: string | null;
    title: string | null;
    published_at: string | null;
  };
}

export default function StatementCard({ statement }: { statement: Statement }) {
  const [copied, setCopied] = useState(false);

  const handleShare = async () => {
    try {
      const url = `${window.location.origin}/statements/${statement.id}`;

      if (navigator.share) {
        await navigator.share({
          url,
          title: statement.source.title ?? "Statement",
        });
        return;
      }

      try {
        await navigator.clipboard.writeText(url);
        setCopied(true);
      } catch {
        window.prompt("Copy this link:", url);
      }
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error("Share failed:", error);
    }
  };

  const date = statement.statement_date
    ? new Date(statement.statement_date).toLocaleDateString("en-IN", {
        day: "numeric",
        month: "short",
        year: "numeric",
      })
    : null;

  return (
    <div
      className="border border-gray-200 rounded-lg p-5 bg-white
      hover:border-green-300 transition-colors"
    >
      {/* Minister */}
      <div className="flex items-start justify-between mb-3">
        <Link href={`/ministers/${statement.minister.id}`} className="group">
          <div className="flex items-center gap-2">
            {/* Avatar — photo or fallback */}
            {statement.minister.image_url ? (
              <div
                className="w-8 h-8 rounded-full overflow-hidden
                border border-gray-200 flex-shrink-0"
              >
                <Image
                  src={statement.minister.image_url}
                  alt={statement.minister.name}
                  width={32}
                  height={32}
                  className="object-cover w-full h-full"
                />
              </div>
            ) : (
              <div
                className="w-8 h-8 rounded-full bg-green-100
                flex items-center justify-center flex-shrink-0"
              >
                <User size={14} className="text-green-700" />
              </div>
            )}

            {/* Name and portfolio */}
            <div>
              <p
                className="font-semibold text-gray-900 text-sm
                group-hover:text-green-700 transition-colors"
              >
                {statement.minister.name}
              </p>
              {statement.minister.portfolio && (
                <p className="text-xs text-gray-500">
                  {statement.minister.portfolio
                    .split(",")[0]
                    .replace("MLA - ", "")}
                </p>
              )}
            </div>
          </div>
        </Link>

        {statement.topic && (
          <span
            className="text-xs bg-green-50 text-green-700
            px-2 py-1 rounded-full border border-green-200"
          >
            {statement.topic}
          </span>
        )}
      </div>

      {/* Statement text */}
      <Link href={`/statements/${statement.id}`}>
        <p
          className="text-gray-800 leading-relaxed mb-4 hover:text-green-700
    transition-colors cursor-pointer"
        >
          {statement.statement_text}
        </p>
      </Link>

      {/* Footer */}
      <div className="flex items-center justify-between pt-3 border-t border-gray-100">
        <div className="flex items-center gap-3 text-xs text-gray-500">
          {date && (
            <span className="flex items-center gap-1">
              <Calendar size={11} />
              {date}
            </span>
          )}
          {statement.source.name && <span>{statement.source.name}</span>}
        </div>

        <div className="flex items-center gap-4 text-xs ">
          <div className="relative group">
            <Link
              href={`/statements/${statement.id}`}
              className="text-blue-500 hover:underline"
            >
              Context
            </Link>

            {statement.context_text && (
              <div
                className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2
                hidden group-hover:block
                bg-white text-blue-500 text-xs rounded px-3 py-2
                w-[340px] shadow-lg z-50"
              >
                {statement.context_text}
              </div>
            )}
          </div>

          {statement.source.url && (
            <div className="relative group">
              <a
                href={statement.source.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 text-xs text-green-700 hover:underline"
              >
                Source <ExternalLink size={10} />
              </a>

              {statement.source.title && (
                <div
                  className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2
                  hidden group-hover:block
                  bg-white text-green-700 text-xs rounded px-3 py-2
                  w-[340px] shadow-lg z-50"
                >
                  {statement.source.title}
                </div>
              )}
            </div>
          )}

          <button
            onClick={handleShare}
            className={cn(
              "flex items-center gap-1 text-xs transition-colors",
              copied ? "text-green-700" : "text-gray-500 hover:text-gray-700",
            )}
          >
            {copied ? <Copy size={10} /> : <Share2 size={10} />}
            {copied ? "Copied!" : "Share"}
          </button>
        </div>
      </div>
    </div>
  );
}
