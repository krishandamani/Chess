import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function LandingPage() {
  return (
    <main className="flex flex-col min-h-screen">
      {/* Nav */}
      <nav className="border-b border-slate-200 bg-white">
        <div className="max-w-5xl mx-auto px-6 h-16 flex items-center justify-between">
          <span className="font-semibold text-lg tracking-tight">repertoire</span>
          <div className="flex gap-3">
            <Link href="/sign-in">
              <Button variant="ghost" size="sm">Sign in</Button>
            </Link>
            <Link href="/sign-up">
              <Button size="sm">Get started free</Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="flex-1 flex flex-col items-center justify-center px-6 py-24 text-center">
        <p className="text-sm font-medium text-slate-500 mb-4 uppercase tracking-widest">
          For the 1200–2000 player who actually wants to improve
        </p>
        <h1 className="text-4xl sm:text-5xl font-bold tracking-tight max-w-2xl leading-tight mb-6">
          Stop solving random puzzles.
          <br />
          <span className="text-slate-500">Train the mistakes you actually make.</span>
        </h1>
        <p className="text-lg text-slate-600 max-w-xl mb-10">
          Repertoire ingests all your Chess.com and Lichess games, finds the
          exact recurring failures costing you rating points, and drills you on
          them with spaced repetition.
        </p>
        <div className="flex gap-4 flex-wrap justify-center">
          <Link href="/sign-up">
            <Button size="lg">Analyze my games — free</Button>
          </Link>
          <a href="#how-it-works">
            <Button size="lg" variant="outline">See how it works</Button>
          </a>
        </div>
      </section>

      {/* Differentiators */}
      <section id="how-it-works" className="bg-white border-t border-slate-200 py-20 px-6">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl font-bold text-center mb-12">
            Not puzzles from your games. <em>Patterns</em> from your games.
          </h2>
          <div className="grid sm:grid-cols-2 gap-8">
            {[
              {
                title: "Cross-game pattern detection",
                body: "\"In 47 games this year you traded into a worse endgame from an equal position. In 31 of them you had a knight on a passive square.\"",
              },
              {
                title: "Opening-aware analysis",
                body: "Every mistake tagged with ECO code and move number. \"Of your 47 Caro-Kann mistakes, 31 came on moves 8–12.\"",
              },
              {
                title: "Brutal, specific reports",
                body: "\"You blunder tactically in 1 of every 7 rapid games. Fix tactics, not positional understanding.\"",
              },
              {
                title: "Volume",
                body: "Ingests all your games — 500, 5,000, 15,000. The more you've played, the more signal we find.",
              },
            ].map(({ title, body }) => (
              <div key={title} className="p-6 rounded-xl border border-slate-200 bg-slate-50">
                <h3 className="font-semibold mb-2">{title}</h3>
                <p className="text-slate-600 text-sm leading-relaxed italic">{body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section className="py-20 px-6">
        <div className="max-w-md mx-auto text-center">
          <h2 className="text-2xl font-bold mb-4">Simple pricing</h2>
          <div className="rounded-xl border border-slate-200 bg-white p-8">
            <p className="text-4xl font-bold mb-1">$9<span className="text-lg font-normal text-slate-500">/mo</span></p>
            <p className="text-slate-500 mb-6">or $79/yr — save $29</p>
            <ul className="text-sm text-left space-y-2 mb-8 text-slate-700">
              {[
                "Unlimited games ingested",
                "All pattern detectors",
                "Spaced repetition drill mode",
                "Weekly email report",
                "ECO opening analysis",
              ].map((f) => (
                <li key={f} className="flex gap-2 items-center">
                  <span className="text-emerald-500">✓</span> {f}
                </li>
              ))}
            </ul>
            <Link href="/sign-up">
              <Button className="w-full" size="lg">Start 14-day free trial</Button>
            </Link>
            <p className="text-xs text-slate-400 mt-3">No credit card required.</p>
          </div>
        </div>
      </section>

      <footer className="border-t border-slate-200 py-6 text-center text-sm text-slate-400">
        © {new Date().getFullYear()} Repertoire. Built for chess improvers.
      </footer>
    </main>
  );
}
