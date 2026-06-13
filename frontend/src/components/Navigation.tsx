"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Search, Users, FileText, Shield, Info, Menu, X } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { useState } from "react";
import { useTheme } from "@/providers/ThemeProvider";
import { Sun, Moon } from "lucide-react";

const navLinks = [
  { href: "/", label: "Statements", icon: FileText },
  { href: "/ministers", label: "Ministers", icon: Users },
  { href: "/search", label: "Search", icon: Search },
  { href: "/about", label: "About", icon: Info },
];

export default function Navigation() {
  const pathname = usePathname();
  const { isLoaded, isModerator } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);
  const { theme, toggleTheme } = useTheme();

  const { data: statsData } = useQuery({
    queryKey: ["queue-stats-nav"],
    queryFn: () => api.getQueueStats(),
    enabled: isLoaded && isModerator,
    refetchInterval: 60000,
    retry: false,
  });

  const pendingCount = statsData?.data?.pending_review || 0;

  const isActive = (href: string) =>
    href === "/"
      ? pathname === "/" || pathname.startsWith("/statements")
      : pathname.startsWith(href);

  return (
    <nav className="border-b border-gray-200 bg-white sticky top-0 z-50 backdrop-blur supports-[backdrop-filter]:bg-white/80">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-14 items-center justify-between gap-2">
          {/* Logo */}
          <Link
            href="/"
            className="flex items-center whitespace-nowrap"
            onClick={() => setMobileOpen(false)}
          >
            <span className="text-lg font-bold text-green-700">open</span>
            <span className="text-lg font-bold text-gray-900">Ministry</span>
            <span className="ml-2 text-xs bg-green-50 text-green-700 px-1.5 py-0.5 rounded border border-green-200 font-medium">
              Kerala
            </span>
          </Link>

          {/* Desktop Links */}
          <div className="hidden sm:flex items-center gap-1">
            {navLinks.map(({ href, label, icon: Icon }) => (
              <Link
                key={href}
                href={href}
                className={cn(
                  "flex items-center gap-1.5 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  isActive(href)
                    ? "bg-green-50 text-green-700"
                    : "text-gray-600 hover:bg-gray-50 hover:text-gray-900",
                )}
              >
                <Icon size={14} className="shrink-0" />
                <span>{label}</span>
              </Link>
            ))}
            {/* Dar/Light Mode */}
            <button
              onClick={toggleTheme}
              className="p-2 rounded-md hover:bg-gray-100 text-gray-600"
              aria-label="Toggle theme"
            >
              {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
            </button>

            {/* Admin */}
            <Link
              href="/admin"
              className={cn(
                "relative flex items-center gap-1.5 rounded-md px-3 py-2 text-sm font-medium transition-colors ml-1",
                pathname.startsWith("/admin") || pathname === "/login"
                  ? "bg-green-700 text-white"
                  : "border border-gray-200 text-gray-600 hover:bg-gray-50",
              )}
            >
              <Shield size={14} className="shrink-0" />
              <span>Admin</span>

              {pendingCount > 0 && (
                <span className="absolute -top-1 -right-1 min-w-5 h-5 px-1 text-[10px] bg-red-500 text-white rounded-full flex items-center justify-center font-bold">
                  {pendingCount > 9 ? "9+" : pendingCount}
                </span>
              )}
            </Link>
          </div>

          {/* Mobile Menu Button */}
          <button
            className="sm:hidden p-2 rounded-md hover:bg-gray-100"
            onClick={() => setMobileOpen((v) => !v)}
            aria-label="Toggle menu"
          >
            {mobileOpen ? <X size={18} /> : <Menu size={18} />}
          </button>
        </div>

        {/* Mobile Menu */}
        {mobileOpen && (
          <div className="sm:hidden mt-2 pb-3 border-t border-gray-100 pt-2 space-y-1">
            {navLinks.map(({ href, label, icon: Icon }) => (
              <Link
                key={href}
                href={href}
                onClick={() => setMobileOpen(false)}
                className={cn(
                  "flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium",
                  isActive(href)
                    ? "bg-green-50 text-green-700"
                    : "text-gray-600 hover:bg-gray-50",
                )}
              >
                <Icon size={16} />
                {label}
              </Link>
            ))}

            <button
              onClick={toggleTheme}
              className="p-2 rounded-md hover:bg-gray-100 text-gray-600"
              aria-label="Toggle theme"
            >
              {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
            </button>

            <Link
              href="/admin"
              onClick={() => setMobileOpen(false)}
              className={cn(
                "relative flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium",
                pathname.startsWith("/admin") || pathname === "/login"
                  ? "bg-green-700 text-white"
                  : "border border-gray-200 text-gray-600 hover:bg-gray-50",
              )}
            >
              <Shield size={16} />
              Admin
              {pendingCount > 0 && (
                <span className="ml-auto min-w-5 h-5 px-1 text-[10px] bg-red-500 text-white rounded-full flex items-center justify-center font-bold">
                  {pendingCount > 9 ? "9+" : pendingCount}
                </span>
              )}
            </Link>
          </div>
        )}
      </div>
    </nav>
  );
}
