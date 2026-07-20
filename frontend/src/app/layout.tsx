import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Navigation from "@/components/Navigation";
import QueryProvider from "@/providers/QueryProvider";
import { ThemeProvider } from "@/providers/ThemeProvider";

export const viewport = {
  width: "device-width",
  initialScale: 1,
  userScalable: true,
};

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "openMinistry (Demo) — Kerala Government Statement Tracker",
    template: "%s | openMinistry (Demo)",
  },
  description:
    "A demo archive showing how openMinistry worked: a searchable public record of verified statements made by Kerala ministers and MLAs. The live site is no longer running; this is a static sample.",
  keywords: [
    "Kerala",
    "ministers",
    "government",
    "statements",
    "transparency",
    "accountability",
    "MLAs",
    "politics",
  ],
  openGraph: {
    title: "openMinistry (Demo) — Kerala Government Statement Tracker",
    description: "Demo archive — verified statements from Kerala ministers and MLAs",
    url: "https://openministry.vercel.app",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`
          ${inter.className}
          bg-background
          text-foreground
          min-h-dvh
          flex
          flex-col
          antialiased
          overflow-x-hidden
        `}
      >
        <QueryProvider>
          <ThemeProvider>
            {/* Demo notice — persistent, not dismissible */}
            <div className="bg-amber-50 border-b border-amber-200 text-amber-900 text-xs sm:text-sm text-center px-3 py-2 dark:bg-amber-950/40 dark:border-amber-900 dark:text-amber-200">
              This is a static <strong>demo</strong> of openMinistry — a sample
              of statements from the archive. The live site is no longer
              running and this data is frozen, not updated.
            </div>

            <Navigation />

            {/* Main content */}
            <main className="flex-1 w-full mx-auto max-w-5xl px-3 sm:px-4 lg:px-8 py-6 sm:py-8">
              {children}
            </main>

            {/* Footer */}
            <footer className="mt-12 sm:mt-16 border-t border-border bg-surface py-8">
              <div className="mx-auto max-w-5xl px-3 sm:px-4 lg:px-8">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-6 text-xs text-muted">
                  {/* Brand */}
                  <div className="text-center sm:text-left">
                    <p className="font-semibold text-foreground text-sm">
                      openMinistry
                    </p>
                    <p className="text-xs text-muted mt-0.5">
                      Promoting transparency in Kerala governance
                    </p>
                  </div>

                  {/* Links */}
                  <div className="flex flex-wrap items-center justify-center sm:justify-end gap-4">
                    <a
                      href="https://github.com/mdsherinoff/openMinistry"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="hover:text-accent transition-colors"
                    >
                      GitHub
                    </a>
                    <span className="text-muted-2">
                      AGPL-3.0 © {new Date().getFullYear()} openMinistry
                    </span>
                  </div>
                </div>
              </div>
            </footer>
          </ThemeProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
