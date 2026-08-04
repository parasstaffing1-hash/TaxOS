import SearchAutocomplete from "@/components/calculator/SearchAutocomplete";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center p-24 bg-gradient-to-b from-blue-50 to-white dark:from-slate-900 dark:to-slate-800">
      <div className="w-full max-w-4xl text-center space-y-8 mt-12">
        <h1 className="text-5xl font-extrabold tracking-tight text-slate-900 dark:text-white sm:text-6xl">
          Universal Tax Calculator
        </h1>
        <p className="text-xl text-slate-600 dark:text-slate-300 max-w-2xl mx-auto">
          Calculate your take-home pay, view tax brackets, and estimate deductions for any city or state.
        </p>

        <div className="pt-8">
          <SearchAutocomplete />
        </div>
      </div>
    </main>
  );
}
