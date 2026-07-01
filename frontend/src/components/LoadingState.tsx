export default function LoadingState() {
  return (
    <div className="py-4">
      <div className="flex items-center justify-center gap-3 text-sm text-zomato-muted">
        <div
          className="h-5 w-5 animate-spin rounded-full border-2 border-gray-200 border-t-zomato-red"
          aria-hidden
        />
        Analyzing reviews and finding your top matches…
      </div>
      <div className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {[1, 2, 3].map((n) => (
          <div key={n} className="overflow-hidden rounded-2xl bg-white shadow-card">
            <div className="aspect-[4/3] animate-pulse bg-gray-200" />
            <div className="space-y-3 p-4">
              <div className="h-5 w-2/3 animate-pulse rounded bg-gray-200" />
              <div className="h-4 w-1/2 animate-pulse rounded bg-gray-100" />
              <div className="h-16 animate-pulse rounded-lg bg-gray-100" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
