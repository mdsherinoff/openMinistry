"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import Link from "next/link";
import { Inbox } from "lucide-react";
import StatsCards from "@/components/moderation/StatsCards";
import ModerationQueue from "@/components/moderation/ModerationQueue";
import FlaggedStatements from "@/components/moderation/FlaggedStatements";
import { LogOut, Shield } from "lucide-react";

export default function AdminPage() {
  const router = useRouter();
  const { isLoaded, isLoggedIn, isModerator, logout } = useAuth();

  useEffect(() => {
    if (isLoaded && !isLoggedIn) {
      router.replace("/login");
    }
  }, [isLoaded, isLoggedIn, router]);

  if (!isLoaded || !isLoggedIn) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <p className="text-muted">Loading...</p>
      </div>
    );
  }

  if (!isModerator) {
    return (
      <div className="text-center py-16">
        <p className="text-danger font-medium">Access denied.</p>
        <p className="text-muted text-sm mt-1">
          You need moderator access to view this page.
        </p>
      </div>
    );
  }

  return (
    <div>
      {/* Page header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Shield size={20} className="text-accent" />
          <h1 className="text-xl font-bold text-foreground">
            Moderation Dashboard
          </h1>
        </div>
        <button
          onClick={logout}
          className="flex items-center gap-1.5 text-sm text-muted
            border border-border px-3 py-1.5 rounded-lg hover:bg-surface-2 hover:text-foreground transition-colors"
        >
          <LogOut size={14} />
          Logout
        </button>
      </div>

      <div className="mb-6">
        <Link
          href="/admin/queue"
          className="flex items-center justify-between p-4
      border border-accent-border rounded-xl bg-accent-soft
      hover:border-accent transition-colors"
        >
          <div className="flex items-center gap-3">
            <Inbox size={20} className="text-accent-soft-fg" />
            <div>
              <p className="font-semibold text-foreground text-sm">
                Article Queue
              </p>
              <p className="text-xs text-accent-soft-fg">
                Review incoming articles and mine statements
              </p>
            </div>
          </div>
          <span className="text-accent-soft-fg text-sm font-medium">
            Open →
          </span>
        </Link>
      </div>

      {/* Stats */}
      <StatsCards />

      {/* Reader-flagged statements to re-evaluate */}
      <FlaggedStatements />

      {/* Queue */}
      <ModerationQueue />
    </div>
  );
}
