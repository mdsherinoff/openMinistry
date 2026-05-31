import { LucideIcon } from "lucide-react";
import Link from "next/link";

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: {
    label: string;
    href: string;
  };
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
}: EmptyStateProps) {
  return (
    <div
      className="text-center py-16 border border-gray-200
      rounded-lg bg-gray-50"
    >
      <Icon size={40} className="text-gray-300 mx-auto mb-3" />
      <p className="text-gray-700 font-medium mb-1">{title}</p>
      <p className="text-gray-500 text-sm mb-4">{description}</p>
      {action && (
        <Link
          href={action.href}
          className="inline-flex items-center gap-1.5 text-sm
            bg-green-700 text-white px-4 py-2 rounded-lg
            hover:bg-green-800 transition-colors"
        >
          {action.label}
        </Link>
      )}
    </div>
  );
}
