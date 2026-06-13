import Link from "next/link";
import { Search, Users, FileText, Shield, ArrowRight } from "lucide-react";

export default function AboutPage() {
  return (
    <div className="py-12">
      {/* Hero */}
      <div className="text-center mb-16">
        <div className="inline-flex items-center gap-2 bg-green-50 dark:bg-green-900/40 text-green-700 dark:text-green-400 px-3 py-1 rounded-full text-sm font-medium mb-4 border border-green-200 dark:border-green-800">
          <Shield size={14} />
          Human verified · Open source · Public interest
        </div>
        <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
          Kerala Government
          <br />
          Statement Tracker
        </h1>
        <p className="text-xl text-gray-500 dark:text-gray-400 max-w-2xl mx-auto mb-8">
          A searchable public archive of statements made by Kerala ministers and
          MLAs taken from newspapers, verified by human moderators, and
          published openly.
        </p>
        <div className="flex items-center justify-center gap-3">
          <Link
            href="/"
            className="inline-flex items-center gap-2 bg-green-700 text-white px-6 py-3 rounded-lg font-medium hover:bg-green-800 transition-colors"
          >
            <FileText size={18} />
            Browse Statements
          </Link>
          <Link
            href="/search"
            className="inline-flex items-center gap-2 border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-300 px-6 py-3 rounded-lg font-medium hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
          >
            <Search size={18} />
            Search
          </Link>
        </div>
      </div>

      {/* Feature cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-16">
        <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-6 bg-white dark:bg-gray-900">
          <FileText
            className="text-green-700 dark:text-green-400 mb-3"
            size={24}
          />
          <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
            Verified Statements
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Every statement is reviewed by a human moderator before publication.
            No automated publishing.
          </p>
        </div>
        <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-6 bg-white dark:bg-gray-900">
          <Users
            className="text-green-700 dark:text-green-400 mb-3"
            size={24}
          />
          <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
            All 140 MLAs
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Tracks statements from all ministers and MLAs of the 16th Kerala
            Legislative Assembly.
          </p>
        </div>
        <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-6 bg-white dark:bg-gray-900">
          <Shield
            className="text-green-700 dark:text-green-400 mb-3"
            size={24}
          />
          <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
            Source Transparency
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Every statement links back to its original news source so you can
            verify it yourself.
          </p>
        </div>
      </div>

      {/* CTA */}
      <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-8 text-center">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
          Browse by Minister
        </h2>
        <p className="text-gray-600 dark:text-gray-400 mb-4">
          See all statements from a specific minister or MLA.
        </p>
        <Link
          href="/ministers"
          className="inline-flex items-center gap-2 bg-green-700 text-white px-5 py-2.5 rounded-lg font-medium hover:bg-green-800 transition-colors"
        >
          View All Ministers
          <ArrowRight size={16} />
        </Link>
      </div>
    </div>
  );
}
