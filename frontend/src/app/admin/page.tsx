"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import Link from "next/link";
import { Inbox } from "lucide-react";
import StatsCards from "@/components/moderation/StatsCards";
import ModerationQueue from "@/components/moderation/ModerationQueue";
import { LogOut, Shield } from "lucide-react";

export default function AdminPage() {
  const router = useRouter();
  const { isLoaded, isLoggedIn, isModerator, logout } = useAuth();

  useEffect(() => {
    if (isLoaded && !isLoggedIn) {
      router.push("/login");
    }
  }, [isLoaded, isLoggedIn, router]);

  if (!isLoaded || !isLoggedIn) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <p className="text-gray-500">Loading...</p>
      </div>
    );
  }

  if (!isModerator) {
    return (
      <div className="text-center py-16">
        <p className="text-red-600 font-medium">Access denied.</p>
        <p className="text-gray-500 text-sm mt-1">
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
          <Shield size={20} className="text-green-700" />
          <h1 className="text-xl font-bold text-white-100">
            Moderation Dashboard
          </h1>
        </div>
        <button
          onClick={logout}
          className="flex items-center gap-1.5 text-sm text-green-400
            border border-gray-200 px-3 py-1.5 rounded-lg hover:bg-gray-50"
        >
          <LogOut size={14} />
          Logout
        </button>
      </div>

      <div className="mb-6">
        <Link
          href="/admin/queue"
          className="flex items-center justify-between p-4
      border border-green-200 rounded-lg bg-green-50
      hover:bg-green-100 transition-colors"
        >
          <div className="flex items-center gap-3">
            <Inbox size={20} className="text-green-700" />
            <div>
              <p className="font-semibold text-green-900 text-sm">
                Article Queue
              </p>
              <p className="text-xs text-green-700">
                Review incoming articles and mine statements
              </p>
            </div>
          </div>
          <span className="text-green-700 text-sm font-medium">Open →</span>
        </Link>
      </div>

      {/* Stats */}
      <StatsCards />

      {/* Queue */}
      <ModerationQueue />
    </div>
  );
}
