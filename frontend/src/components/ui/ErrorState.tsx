import { AlertCircle, RefreshCw } from "lucide-react";

interface ErrorStateProps {
  message?: string;
  onRetry?: () => void;
}

export function ErrorState({
  message = "Something went wrong",
  onRetry,
}: ErrorStateProps) {
  return (
    <div
      className="text-center py-12 border border-danger-border
      rounded-xl bg-danger-soft"
    >
      <AlertCircle size={36} className="text-danger mx-auto mb-3" />
      <p className="text-danger font-medium mb-1">{message}</p>
      <p className="text-danger/80 text-sm mb-4">
        Please try again or check your connection
      </p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="inline-flex items-center gap-1.5 text-sm
            border border-danger-border text-danger px-4 py-2
            rounded-lg hover:bg-danger/10 transition-colors"
        >
          <RefreshCw size={14} />
          Try again
        </button>
      )}
    </div>
  );
}
