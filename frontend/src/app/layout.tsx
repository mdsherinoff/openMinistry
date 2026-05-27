import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Navigation from "../../components/Navigation";
import QueryProvider from "../../providers/QueryProvider";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "openMinistry",
  description:
    "A public archive of statements made by government ministers and representatives.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <QueryProvider>
          <Navigation />
          <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
            {children}
          </main>
          <footer className="mt-16 border-t border-gray-400 py-8 text-center text-sm text-white/60">
            openMinistry Promote Government Transparency
          </footer>
        </QueryProvider>
      </body>
    </html>
  );
}
