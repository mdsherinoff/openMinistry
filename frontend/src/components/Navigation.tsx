"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Search, Users, FileText, Shield, Info } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";

const navLinks = [
  { href: "/", label: "Statements", icon: FileText },
  { href: "/ministers", label: "Ministers", icon: Users },
  { href: "/search", label: "Search", icon: Search },
  { href: "/about", label: "About", icon: Info },
];

export default function Navigation() {
  const pathname = usePathname();
  const { isLoaded, isModerator } = useAuth();

  // Get pending queue count for badge
  const { data: statsData } = useQuery({
    queryKey: ["queue-stats-nav"],
    queryFn: () => api.getQueueStats(),
    enabled: isLoaded && isModerator,
    refetchInterval: 60000,
    retry: false,
  });
  const pendingCount = statsData?.data?.pending_review || 0;

  return (
    <nav className="border-b border-gray-200 bg-white sticky top-0 z-50">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-14 items-center justify-between">
          {/* Logo */}
          <Link href="/" className="flex items-center">
            <span className="text-lg font-bold text-green-700">open</span>
            <span className="text-lg font-bold text-gray-900">Ministry</span>
            <span
              className="ml-2 text-xs bg-green-50 text-green-700
              px-1.5 py-0.5 rounded border border-green-200 font-medium"
            >
              Kerala
            </span>
          </Link>

          {/* Links */}
          <div className="flex items-center gap-1">
            {navLinks.map(({ href, label, icon: Icon }) => (
              <Link
                key={href}
                href={href}
                className={cn(
                  "flex items-center gap-1.5 rounded-md px-3 py-2",
                  "text-sm font-medium transition-colors",
                  pathname === href ||
                    (href !== "/" && pathname.startsWith(href + "/")) ||
                    (href === "/" && pathname.startsWith("/statements"))
                    ? "bg-green-50 text-green-700"
                    : "text-gray-600 hover:bg-gray-50 hover:text-gray-900",
                )}
              >
                <Icon size={14} />
                <span className="hidden sm:inline">{label}</span>
              </Link>
            ))}

            {/* Admin */}
            <Link
              href="/admin"
              className={cn(
                "relative flex items-center gap-1.5 rounded-md px-3 py-2",
                "text-sm font-medium transition-colors ml-1",
                pathname.startsWith("/admin") || pathname === "/login"
                  ? "bg-green-700 text-white"
                  : "border border-gray-200 text-gray-600 hover:bg-gray-50",
              )}
            >
              <Shield size={14} />
              <span className="hidden sm:inline">Admin</span>
              {pendingCount > 0 && (
                <span
                  className="absolute -top-1 -right-1 w-4 h-4
                  bg-red-500 text-white text-xs rounded-full
                  flex items-center justify-center font-bold"
                >
                  {pendingCount > 9 ? "9+" : pendingCount}
                </span>
              )}
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}
