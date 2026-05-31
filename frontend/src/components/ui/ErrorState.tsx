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
      className="text-center py-12 border border-red-100
      rounded-lg bg-red-50"
    >
      <AlertCircle size={36} className="text-red-400 mx-auto mb-3" />
      <p className="text-red-700 font-medium mb-1">{message}</p>
      <p className="text-red-500 text-sm mb-4">
        Please try again or check your connection
      </p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="inline-flex items-center gap-1.5 text-sm
            border border-red-300 text-red-600 px-4 py-2
            rounded-lg hover:bg-red-100 transition-colors"
        >
          <RefreshCw size={14} />
          Try again
        </button>
      )}
    </div>
  );
}
