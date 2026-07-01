interface Props {
  summary: string;
  llmUsed: boolean;
  filtersRelaxed: boolean;
  relaxationSteps: string[];
  candidateCount: number;
  processingMs: number;
}

export default function SummaryBanner({
  summary,
  llmUsed,
  filtersRelaxed,
  relaxationSteps,
  candidateCount,
  processingMs,
}: Props) {
  return (
    <section className="mb-6 rounded-xl border border-gray-100 bg-white px-4 py-4 shadow-sm sm:px-5">
      <p className="text-sm leading-relaxed text-zomato-dark sm:text-base">{summary}</p>
      <div className="mt-3 flex flex-wrap gap-2">
        <span
          className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
            llmUsed ? "bg-green-50 text-zomato-rating" : "bg-amber-50 text-amber-700"
          }`}
        >
          {llmUsed ? "Neural ranking (Groq)" : "Rule-based fallback"}
        </span>
        <span className="rounded-full bg-gray-50 px-2.5 py-0.5 text-xs font-medium text-zomato-muted">
          {candidateCount} candidates analyzed
        </span>
        <span className="rounded-full bg-gray-50 px-2.5 py-0.5 text-xs font-medium text-zomato-muted">
          {processingMs}ms
        </span>
        {filtersRelaxed &&
          (relaxationSteps.length > 0 ? (
            relaxationSteps.map((step) => (
              <span
                key={step}
                className="rounded-full bg-amber-50 px-2.5 py-0.5 text-xs font-medium text-amber-700"
              >
                {step}
              </span>
            ))
          ) : (
            <span className="rounded-full bg-amber-50 px-2.5 py-0.5 text-xs font-medium text-amber-700">
              Filters relaxed
            </span>
          ))}
      </div>
    </section>
  );
}
