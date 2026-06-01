import { ExternalLink, Calendar, User } from "lucide-react";
import Image from "next/image";
import Link from "next/link";

interface Statement {
  id: number;
  statement_text: string;
  statement_date: string | null;
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
      <p className="text-gray-800 leading-relaxed mb-4">
        {statement.statement_text}
      </p>

      {/* Footer */}
      <div
        className="flex items-center justify-between
        pt-3 border-t border-gray-100"
      >
        <div className="flex items-center gap-3 text-xs text-gray-500">
          {date && (
            <span className="flex items-center gap-1">
              <Calendar size={11} />
              {date}
            </span>
          )}
          {statement.source.name && <span>{statement.source.name}</span>}
        </div>

        {statement.source.url && (
          <a
            href={statement.source.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-xs text-green-700 hover:underline"
          >
            Source <ExternalLink size={10} />
          </a>
        )}
      </div>
    </div>
  );
}
