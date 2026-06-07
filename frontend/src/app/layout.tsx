import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Navigation from "@/components/Navigation";
import QueryProvider from "@/providers/QueryProvider";

const inter = Inter({ subsets: ["latin"] });

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
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-gray-50 min-h-screen`}>
        <QueryProvider>
          <Navigation />
          <main
            className="mx-auto max-w-5xl px-4 py-8
            sm:px-6 lg:px-8"
          >
            {children}
          </main>
          <footer
            className="mt-16 border-t border-gray-200
            bg-white py-8"
          >
            <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
              <div
                className="flex flex-col sm:flex-row items-center
                justify-between gap-4"
              >
                <div>
                  <p className="font-semibold text-gray-900 text-sm">
                    openMinistry
                  </p>
                  <p className="text-xs text-gray-500 mt-0.5">
                    Promoting transparency in Kerala governance
                  </p>
                </div>
                <div
                  className="flex items-center gap-4
                  text-xs text-gray-500"
                >
                  <a
                    href="https://openministry.live/docs"
                    rel="noopener noreferrer"
                    className="hover:text-green-700 transition-colors"
                  >
                    API Docs
                  </a>

                  <a
                    href="https://github.com/mdsherinoff/openMinistry"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hover:text-green-700 transition-colors"
                  >
                    GitHub
                  </a>
                  <span>AGPL-3.0</span>
                </div>
              </div>
            </div>
          </footer>
        </QueryProvider>
      </body>
    </html>
  );
}
