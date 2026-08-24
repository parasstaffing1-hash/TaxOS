"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { ArrowRight, Search } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export default function SearchAutocomplete() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<{ name: string; url: string }[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    const delayDebounceFn = setTimeout(async () => {
      if (query.length >= 2) {
        setLoading(true);
        try {
          const res = await fetch(`${API_BASE}/seo/search?q=${encodeURIComponent(query)}`);
          if (res.ok) {
            const data = await res.json();
            setResults(data);
            setIsOpen(true);
          }
        } catch (err) {
          console.error("Search failed", err);
        } finally {
          setLoading(false);
        }
      } else {
        setResults([]);
        setIsOpen(false);
      }
    }, 300);

    return () => clearTimeout(delayDebounceFn);
  }, [query]);

  return (
    <div ref={wrapperRef} className="relative z-50 w-full">
      <div className="relative">
        <input
          type="text"
          className="w-full rounded-md border border-[#dedbd5] bg-white py-2.5 pl-10 pr-10 text-sm text-[#4d4942] shadow-none outline-none transition-colors placeholder:text-[#aaa69f] focus:border-[#8da994] focus:ring-2 focus:ring-[#dfece1]"
          placeholder="Search locations or calculators"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => {
            if (results.length > 0) setIsOpen(true);
          }}
        />
        <Search className="absolute left-3 top-3 h-4 w-4 text-[#aaa69f]" />
        {loading && (
          <div className="absolute right-4 top-3.5">
            <div className="h-4 w-4 animate-spin rounded-full border-2 border-[#d9d5cd] border-b-[#6f8f76]"></div>
          </div>
        )}
      </div>

      {isOpen && results.length > 0 && (
        <div className="absolute mt-2 w-full overflow-hidden rounded-lg border border-[#e8e6e1] bg-white shadow-[0_12px_30px_rgba(55,53,47,0.12)]">
          <ul className="max-h-80 overflow-y-auto py-1.5">
            {results.map((result, idx) => (
              <li key={idx}>
                <Link
                  href={result.url}
                  className="group flex items-center justify-between px-3.5 py-2.5 text-sm text-[#6f6a62] transition-colors hover:bg-[#faf9f7] hover:text-[#37352f]"
                  onClick={() => setIsOpen(false)}
                >
                  <span className="flex min-w-0 items-center gap-2.5"><Search className="h-3.5 w-3.5 shrink-0 text-[#aaa69f]" /><span className="truncate">{result.name}</span></span>
                  <ArrowRight className="h-3.5 w-3.5 shrink-0 text-[#c1bdb5] transition-transform group-hover:translate-x-0.5" />
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
