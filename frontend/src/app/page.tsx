import Link from "next/link";
import { Search, Users, FileText, Shield } from "lucide-react";

export default function HomePage() {
  return (
    <div className="py-12">
      {/* Hero */}
      <div className="text-center mb-16">
        <h1 className="text-4xl font-bold text-white-900 mb-4">
          Promote Government Transparency
        </h1>
        <p className="text-xl text-gray-500 max-w-2xl mx-auto mb-8">
          A searchable public archive of statements made by ministers and
          government representatives; verified by human moderators.
        </p>
        <Link
          href="/search"
          className="inline-flex items-center gap-2 bg-green-700 text-white px-6 py-3 rounded-lg font-medium hover:bg-green-800 transition-colors"
        >
          <Search size={18} />
          Search Statements
        </Link>
      </div>

      {/* Feature cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-16">
        <div className="border border-gray-400 rounded-lg p-6">
          <FileText className="text-green-700 mb-3" size={24} />
          <h3 className="font-semibold text-white-10 mb-2">
            Verified Statements
          </h3>
          <p className="text-sm text-gray-500">
            Every statement is reviewed by a human moderator before publication.
            No automated publishing.
          </p>
        </div>
        <div className="border border-gray-400 rounded-lg p-6">
          <Users className="text-green-700 mb-3" size={24} />
          <h3 className="font-semibold text-white-10 mb-2">
            Minister Profiles
          </h3>
          <p className="text-sm text-gray-500">
            Browse statements by minister, track their positions over time, and
            see topic trends.
          </p>
        </div>
        <div className="border border-gray-400 rounded-lg p-6">
          <Shield className="text-green-700 mb-3" size={24} />
          <h3 className="font-semibold text-white-10 mb-2">
            Source Transparency
          </h3>
          <p className="text-sm text-gray-500">
            Every statement links back to its original news source so you can
            verify it yourself.
          </p>
        </div>
      </div>
    </div>
  );
}
