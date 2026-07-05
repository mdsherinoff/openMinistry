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
      className="text-center py-16 border border-dashed border-border
      rounded-xl bg-surface-2/50"
    >
      <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-surface-2">
        <Icon size={26} className="text-muted-2" />
      </div>
      <p className="text-foreground font-medium mb-1">{title}</p>
      <p className="text-muted text-sm mb-4">{description}</p>
      {action && (
        <Link
          href={action.href}
          className="inline-flex items-center gap-1.5 text-sm font-medium
            bg-accent text-accent-contrast px-4 py-2 rounded-lg
            hover:bg-accent-hover transition-colors"
        >
          {action.label}
        </Link>
      )}
    </div>
  );
}
