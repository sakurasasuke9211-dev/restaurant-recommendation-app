import Navbar from "./Navbar";

const HERO_FOOD_IMAGE =
  "https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=1600&q=80";

interface Props {
  restaurantCount: number | null;
  llmAvailable: boolean | null;
}

export default function HeroSection({ restaurantCount, llmAvailable }: Props) {
  return (
    <section className="relative overflow-hidden">
      <div
        className="absolute inset-0 bg-cover bg-center"
        style={{ backgroundImage: `url('${HERO_FOOD_IMAGE}')` }}
        aria-hidden
      />
      <div
        className="absolute inset-0 bg-gradient-to-b from-black/65 via-black/50 to-zomato-cream"
        aria-hidden
      />

      <div className="relative z-10">
        <Navbar overBanner />

        <div className="mx-auto max-w-4xl px-4 pb-12 pt-10 text-center sm:px-6 sm:pb-14 sm:pt-12">
          <h1 className="text-3xl font-bold tracking-tight text-white sm:text-4xl md:text-5xl">
            What are you <span className="gradient-craving">craving</span> today?
          </h1>
          <p className="mx-auto mt-3 max-w-xl text-sm text-white/80 sm:text-base">
            Our neural engine analyzes thousands of reviews to find your perfect flavor match.
          </p>

          {(restaurantCount != null || llmAvailable != null) && (
            <div className="mt-4 flex flex-wrap justify-center gap-2">
              {restaurantCount != null && (
                <span className="rounded-full bg-white/15 px-3 py-1 text-xs font-medium text-white ring-1 ring-white/20 backdrop-blur-sm">
                  {restaurantCount.toLocaleString()} restaurants indexed
                </span>
              )}
              {llmAvailable != null && (
                <span
                  className={`rounded-full px-3 py-1 text-xs font-medium ring-1 backdrop-blur-sm ${
                    llmAvailable
                      ? "bg-green-500/20 text-green-100 ring-green-400/30"
                      : "bg-amber-500/20 text-amber-100 ring-amber-400/30"
                  }`}
                >
                  {llmAvailable ? "Groq AI active" : "Fallback ranking mode"}
                </span>
              )}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
