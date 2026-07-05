import type { Metadata } from "next";
import { Inter } from "next/font/google";
import Script from "next/script";
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
    default: "openMinistry — Kerala Government Statement Tracker",
    template: "%s | openMinistry",
  },
  description:
    "A searchable public archive of verified statements made by Kerala ministers and MLAs. Human-verified, open source.",
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
    title: "openMinistry — Kerala Government Statement Tracker",
    description: "Verified statements from Kerala ministers and MLAs",
    url: "https://openministry.live",
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
        {/* Google Analytics */}
        <Script
          src="https://www.googletagmanager.com/gtag/js?id=G-VF0WRFHDZT"
          strategy="afterInteractive"
        />
        <Script id="google-analytics" strategy="afterInteractive">
          {`
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            gtag('config', 'G-VF0WRFHDZT');
          `}
        </Script>

        <QueryProvider>
          <ThemeProvider>
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
                      href="https://openministry.live/docs"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="hover:text-accent transition-colors"
                    >
                      API Docs
                    </a>
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
