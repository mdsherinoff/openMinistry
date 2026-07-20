"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Search, Users, FileText, Info, Menu, X, Sun, Moon } from "lucide-react";
import { useState, useEffect } from "react";
import { useTheme } from "@/providers/ThemeProvider";

const navLinks = [
  { href: "/", label: "Statements", icon: FileText },
  { href: "/ministers", label: "Ministers", icon: Users },
  { href: "/search", label: "Search", icon: Search },
  { href: "/about", label: "About", icon: Info },
];

export default function Navigation() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const { theme, toggleTheme } = useTheme();

  useEffect(() => {
    const id = setTimeout(() => setMobileOpen(false), 0);
    return () => clearTimeout(id);
  }, [pathname]);

  const isActive = (href: string) =>
    href === "/"
      ? pathname === "/" || pathname.startsWith("/statements")
      : pathname.startsWith(href);

  return (
    <nav className="border-b border-border bg-surface/80 sticky top-0 z-50 backdrop-blur supports-[backdrop-filter]:bg-surface/70">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-14 items-center justify-between gap-2">
          {/* Logo */}
          <Link
            href="/"
            className="flex items-center whitespace-nowrap"
            onClick={() => setMobileOpen(false)}
          >
            <span className="text-lg font-bold text-accent">open</span>
            <span className="text-lg font-bold text-foreground">Ministry</span>
            <span className="ml-2 text-xs bg-accent-soft text-accent-soft-fg px-1.5 py-0.5 rounded border border-accent-border font-medium">
              Kerala
            </span>
            <span className="ml-1.5 text-xs bg-amber-100 text-amber-800 px-1.5 py-0.5 rounded border border-amber-300 font-medium dark:bg-amber-900/40 dark:text-amber-300 dark:border-amber-800">
              Demo
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
                    ? "bg-accent-soft text-accent-soft-fg"
                    : "text-muted hover:bg-surface-2 hover:text-foreground",
                )}
              >
                <Icon size={14} className="shrink-0" />
                <span>{label}</span>
              </Link>
            ))}

            {/* Dark/Light Mode for desktop */}
            <button
              onClick={toggleTheme}
              title={
                theme === "dark"
                  ? "Switch to light mode"
                  : "Switch to dark mode"
              }
              aria-label={
                theme === "dark"
                  ? "Switch to light mode"
                  : "Switch to dark mode"
              }
              className="p-2 rounded-md hover:bg-surface-2 text-muted hover:text-foreground"
            >
              {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
            </button>
          </div>

          {/* Mobile Menu Button */}
          <button
            className="sm:hidden p-2 rounded-md hover:bg-surface-2 text-muted hover:text-foreground"
            onClick={() => setMobileOpen((v) => !v)}
            aria-label="Toggle menu"
          >
            {mobileOpen ? <X size={18} /> : <Menu size={18} />}
          </button>
        </div>

        {/* Mobile Menu */}
        {mobileOpen && (
          <div className="sm:hidden mt-2 pb-3 border-t border-border pt-2 space-y-1">
            {navLinks.map(({ href, label, icon: Icon }) => (
              <Link
                key={href}
                href={href}
                onClick={() => setMobileOpen(false)}
                className={cn(
                  "flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium",
                  isActive(href)
                    ? "bg-accent-soft text-accent-soft-fg"
                    : "text-muted hover:bg-surface-2 hover:text-foreground",
                )}
              >
                <Icon size={16} />
                {label}
              </Link>
            ))}

            {/* Dark/Light Mode for mobile */}
            <button
              onClick={toggleTheme}
              className="w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium text-muted hover:bg-surface-2 hover:text-foreground"
            >
              {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
              <span>Appearance</span>
              <span className="ml-auto text-xs text-muted-2 bg-surface-2 rounded-full px-2 py-0.5 font-normal">
                {theme === "dark" ? "Dark" : "Light"}
              </span>
            </button>
          </div>
        )}
      </div>
    </nav>
  );
}
