"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
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

      {/* Stats */}
      <StatsCards />

      {/* Queue */}
      <ModerationQueue />
    </div>
  );
}
