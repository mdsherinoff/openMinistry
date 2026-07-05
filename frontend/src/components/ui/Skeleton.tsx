import { cn } from "@/lib/utils";

interface SkeletonProps {
  className?: string;
}

export function Skeleton({ className }: SkeletonProps) {
  return (
    <div className={cn("animate-pulse rounded-md bg-surface-2", className)} />
  );
}

export function StatementSkeleton() {
  return (
    <div className="rounded-xl border border-border p-5 bg-surface shadow-sm">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2.5">
          <Skeleton className="w-9 h-9 rounded-full" />
          <div>
            <Skeleton className="h-4 w-32 mb-1.5" />
            <Skeleton className="h-3 w-24" />
          </div>
        </div>
        <Skeleton className="h-5 w-16 rounded-full" />
      </div>
      <Skeleton className="h-4 w-full mb-2" />
      <Skeleton className="h-4 w-full mb-2" />
      <Skeleton className="h-4 w-3/4 mb-4" />
      <div className="flex items-center gap-3 pt-3 border-t border-border">
        <Skeleton className="h-3 w-20" />
        <Skeleton className="h-3 w-24" />
      </div>
    </div>
  );
}

export function MinisterCardSkeleton() {
  return (
    <div className="rounded-xl border border-border p-4 bg-surface shadow-sm">
      <div className="flex items-start justify-between mb-2">
        <Skeleton className="w-9 h-9 rounded-full" />
        <Skeleton className="h-5 w-16 rounded-full" />
      </div>
      <Skeleton className="h-4 w-36 mb-2" />
      <Skeleton className="h-3 w-28 mb-1" />
      <Skeleton className="h-3 w-20" />
    </div>
  );
}
