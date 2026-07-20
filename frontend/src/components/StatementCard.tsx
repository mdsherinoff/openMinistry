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
      className="group/card rounded-xl border border-border bg-surface p-5
      shadow-sm transition-all duration-200
      hover:border-accent-border hover:shadow-md hover:-translate-y-0.5"
    >
      {/* Minister */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <Link href={`/ministers/${statement.minister.id}`} className="group">
          <div className="flex items-center gap-2.5">
            {/* Avatar — photo or fallback */}
            {statement.minister.image_url ? (
              <div
                className="w-9 h-9 rounded-full overflow-hidden
                ring-2 ring-border flex-shrink-0"
              >
                <Image
                  src={statement.minister.image_url}
                  alt={statement.minister.name}
                  width={36}
                  height={36}
                  className="object-cover w-full h-full"
                />
              </div>
            ) : (
              <div
                className="w-9 h-9 rounded-full bg-accent-soft
                flex items-center justify-center flex-shrink-0"
              >
                <User size={15} className="text-accent-soft-fg" />
              </div>
            )}

            {/* Name and portfolio */}
            <div>
              <p
                className="font-semibold text-foreground text-sm
                group-hover:text-accent transition-colors"
              >
                {statement.minister.name}
              </p>
              {statement.minister.portfolio && (
                <p className="text-xs text-muted">
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
            className="shrink-0 text-xs font-medium bg-accent-soft text-accent-soft-fg
            px-2.5 py-1 rounded-full border border-accent-border"
          >
            {statement.topic}
          </span>
        )}
      </div>

      {/* Statement text */}
      <Link href={`/statements/${statement.id}`}>
        <p
          className="text-[15px] text-foreground/90 leading-relaxed mb-4
          hover:text-accent transition-colors cursor-pointer"
        >
          {statement.statement_text}
        </p>
      </Link>

      {/* Footer */}
      <div className="flex items-center justify-between pt-3 border-t border-border">
        <div className="flex items-center gap-3 text-xs text-muted">
          {date && (
            <span className="flex items-center gap-1">
              <Calendar size={11} />
              {date}
            </span>
          )}
          {statement.source.name && <span>{statement.source.name}</span>}
        </div>

        <div className="flex items-center gap-4 text-xs">
          <div className="relative group">
            <Link
              href={`/statements/${statement.id}`}
              className="text-muted hover:text-foreground transition-colors"
            >
              Context
            </Link>

            {statement.context_text && (
              <div
                className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2
                hidden group-hover:block
                bg-surface text-foreground text-xs rounded-lg px-3 py-2
                w-[340px] shadow-lg border border-border z-50"
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
                className="flex items-center gap-1 text-xs text-accent hover:underline"
              >
                Source <ExternalLink size={10} />
              </a>

              {statement.source.title && (
                <div
                  className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2
                  hidden group-hover:block
                  bg-surface text-foreground text-xs rounded-lg px-3 py-2
                  w-[340px] shadow-lg border border-border z-50"
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
              copied ? "text-accent" : "text-muted hover:text-foreground",
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
