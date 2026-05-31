"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Search, Users, FileText, Shield } from "lucide-react";

const navLinks = [
  { href: "/statements", label: "Statements", icon: FileText },
  { href: "/ministers", label: "Ministers", icon: Users },
  { href: "/search", label: "Search", icon: Search },
];

export default function Navigation() {
  const pathname = usePathname();

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
                  pathname === href || pathname.startsWith(href + "/")
                    ? "bg-green-50 text-green-700"
                    : "text-gray-600 hover:bg-gray-50 hover:text-gray-900",
                )}
              >
                <Icon size={14} />
                <span className="hidden sm:inline">{label}</span>
              </Link>
            ))}
            <Link
              href="/admin"
              className={cn(
                "flex items-center gap-1.5 rounded-md px-3 py-2",
                "text-sm font-medium transition-colors ml-1",
                pathname.startsWith("/admin") || pathname === "/login"
                  ? "bg-green-700 text-white"
                  : "border border-gray-200 text-gray-600 hover:bg-gray-50",
              )}
            >
              <Shield size={14} />
              <span className="hidden sm:inline">Admin</span>
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}
