import Link from "next/link";

/**
 * Analytics is deliberately not part of the public calculator release. The
 * corresponding API is mounted only when internal tools are enabled and is
 * protected by an administrator check. Keeping this page explicit prevents a
 * public-facing demo dashboard from presenting unverified jurisdictions.
 */
export default function AnalyticsPage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-2xl items-center px-6 py-16">
      <section className="rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
        <p className="text-sm font-medium uppercase tracking-wide text-slate-500">TaxOS</p>
        <h1 className="mt-2 text-3xl font-semibold text-slate-900">Analytics is not enabled</h1>
        <p className="mt-4 text-slate-600">
          The public release includes verified tax-calculation workflows. Analytics remains an
          internal, administrator-only capability while its data coverage is expanded.
        </p>
        <Link className="mt-6 inline-block text-blue-700 hover:underline" href="/">
          Return to the calculator
        </Link>
      </section>
    </main>
  );
}
