interface Props {
  overBanner?: boolean;
}

const NAV_LINKS = [
  { label: "Discover", active: true },
  { label: "Memories", active: false },
  { label: "Concierge", active: false },
] as const;

function IconBell() {
  return (
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.4-1.4A2 2 0 0118 14.2V11a6 6 0 10-12 0v3.2a2 2 0 01-.6 1.4L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
    </svg>
  );
}

function IconCart() {
  return (
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.3 9.7a1 1 0 001 1.3h12.6a1 1 0 001-1.3L17 13M9 19.5a1.5 1.5 0 103 0 1.5 1.5 0 00-3 0zm8 0a1.5 1.5 0 103 0 1.5 1.5 0 00-3 0z" />
    </svg>
  );
}

export default function Navbar({ overBanner = false }: Props) {
  return (
    <header
      className={
        overBanner
          ? "border-b border-white/10 bg-black/20 backdrop-blur-md"
          : "sticky top-0 z-50 border-b border-gray-100 bg-white"
      }
    >
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 sm:px-6">
        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-zomato-red text-white">
            <svg className="h-5 w-5" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
              <path d="M11 9H9V2H7v7H5V2H3v7c0 2.12 1.66 3.84 3.75 3.97V22h2.5v-9.03C11.34 12.84 13 11.12 13 9V2h-2v7zm5-5v7h2.5V2H16zm5 0v7c0 2.12-1.66 3.84-3.75 3.97V22H20v-9.03C22.34 12.84 24 11.12 24 9V2h-2.5v7H21V2h-2z" />
            </svg>
          </div>
          <span
            className={`font-display text-xl font-bold ${
              overBanner ? "text-white" : "text-zomato-brand"
            }`}
          >
            Zomato AI
          </span>
        </div>

        <nav className="hidden items-center gap-8 md:flex" aria-label="Main">
          {NAV_LINKS.map(({ label, active }) => (
            <a
              key={label}
              href="#"
              className={`relative text-sm font-medium transition ${
                overBanner
                  ? active
                    ? "text-white"
                    : "text-white/70 hover:text-white"
                  : active
                    ? "text-zomato-dark"
                    : "text-zomato-muted hover:text-zomato-red"
              }`}
              onClick={(e) => e.preventDefault()}
            >
              {label}
              {active && (
                <span
                  className={`absolute -bottom-3.5 left-0 right-0 h-0.5 rounded-full ${
                    overBanner ? "bg-white" : "bg-zomato-red"
                  }`}
                />
              )}
            </a>
          ))}
        </nav>

        <div
          className={`flex items-center gap-3 ${
            overBanner ? "text-white/80" : "text-zomato-muted"
          }`}
        >
          <button
            type="button"
            className={`rounded-full p-2 ${
              overBanner ? "hover:bg-white/10 hover:text-white" : "hover:bg-gray-100 hover:text-zomato-dark"
            }`}
            aria-label="Notifications"
          >
            <IconBell />
          </button>
          <button
            type="button"
            className={`rounded-full p-2 ${
              overBanner ? "hover:bg-white/10 hover:text-white" : "hover:bg-gray-100 hover:text-zomato-dark"
            }`}
            aria-label="Cart"
          >
            <IconCart />
          </button>
          <div
            className="h-9 w-9 rounded-full bg-gradient-to-br from-amber-200 to-orange-400 ring-2 ring-white/80"
            aria-label="Profile"
            role="img"
          />
        </div>
      </div>
    </header>
  );
}
