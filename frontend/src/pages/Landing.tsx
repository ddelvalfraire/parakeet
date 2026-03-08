import { useState, useEffect, useRef } from "react"
import { Link } from "react-router"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Zap,
  Radar,
  Crosshair,
  ShieldCheck,
  Bell,
  Layers,
  Search,
  CheckCircle2,
  FileText,
  ArrowRight,
  ChevronRight,
  Clock,
  Activity,
  TrendingDown,
  Terminal,
} from "lucide-react"
import parakeetLogo from "@/assets/Parakeet-logo.png"

// ── Incident simulation ───────────────────────────────────────

const simulationLines = [
  { text: "\u25b8 Alert received \u2014 PagerDuty #38291", type: "system" },
  { text: "\u25b8 Incident INC-2847 created", type: "system" },
  { text: "", type: "spacer" },
  { text: "\u25b8 agent:triage \u2014 classifying severity\u2026", type: "agent" },
  { text: "  P1 Critical \u2014 payment processing failure", type: "result" },
  { text: "  Affected: checkout-svc, payment-api, billing-worker", type: "result" },
  { text: "", type: "spacer" },
  { text: "\u25b8 agent:investigate \u2014 scanning 1,247 log entries\u2026", type: "agent" },
  { text: "\u25b8 agent:investigate \u2014 correlating deploy history\u2026", type: "agent" },
  { text: "  Anomaly: deploy #4521 (payment-api v2.3.1) \u2014 2h ago", type: "result" },
  { text: "  Blast radius: 3 services, ~12k req/min affected", type: "result" },
  { text: "", type: "spacer" },
  { text: "\u25b8 agent:root-cause \u2014 analyzing evidence chain\u2026", type: "agent" },
  { text: "  Root cause: memory leak in payment-api v2.3.1", type: "result" },
  { text: "  Confidence: 94% \u2014 3 corroborating signals", type: "result" },
  { text: "", type: "spacer" },
  { text: "\u25b8 Fix recommended: rollback to payment-api v2.3.0", type: "agent" },
  { text: "  Risk: low \u2014 previous version stable for 14 days", type: "result" },
  { text: "", type: "spacer" },
  { text: "\u2713 Fix approved by operator", type: "success" },
  { text: "\u2713 Rollback complete \u2014 all health checks passing", type: "success" },
  { text: "\u2713 Incident resolved \u2014 MTTR: 4m 12s", type: "success" },
] as const

function getSimStatus(idx: number) {
  if (idx <= 2) return { label: "Detected", color: "text-red-400", dot: "bg-red-500", pulse: true }
  if (idx <= 6) return { label: "Triaging", color: "text-purple-400", dot: "bg-purple-500", pulse: true }
  if (idx <= 11) return { label: "Investigating", color: "text-blue-400", dot: "bg-blue-500", pulse: true }
  if (idx <= 15) return { label: "Root Cause", color: "text-indigo-400", dot: "bg-indigo-500", pulse: true }
  if (idx <= 18) return { label: "Awaiting Approval", color: "text-amber-400", dot: "bg-amber-500", pulse: true }
  return { label: "Resolved", color: "text-green-400", dot: "bg-green-500", pulse: false }
}

function IncidentSimulation() {
  const [count, setCount] = useState(0)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (count >= simulationLines.length) {
      const t = setTimeout(() => setCount(0), 5000)
      return () => clearTimeout(t)
    }
    const delay = simulationLines[count].type === "spacer" ? 150 : 650
    const t = setTimeout(() => setCount((c) => c + 1), delay)
    return () => clearTimeout(t)
  }, [count])

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" })
  }, [count])

  const status = getSimStatus(count)
  const visible = simulationLines.slice(0, count)

  return (
    <div className="w-full rounded-xl border border-white/[0.08] bg-white/[0.02] shadow-2xl shadow-emerald-500/[0.04] overflow-hidden">
      {/* Card header */}
      <div className="flex items-center justify-between border-b border-white/[0.06] px-4 py-3">
        <div className="flex items-center gap-2.5">
          <Terminal className="size-3.5 text-gray-500" />
          <span className="font-mono text-xs text-gray-400">INC-2847</span>
          <Badge className="bg-red-600 text-white text-[10px] leading-none px-1.5 py-0.5">
            P1
          </Badge>
        </div>
        <div className="flex items-center gap-1.5">
          <span
            className={cn(
              "size-1.5 rounded-full",
              status.dot,
              status.pulse && "animate-pulse",
            )}
          />
          <span className={cn("text-[11px] font-medium", status.color)}>
            {status.label}
          </span>
        </div>
      </div>

      {/* Terminal body */}
      <div ref={scrollRef} className="h-[340px] overflow-y-auto p-4 font-mono text-[11px] leading-[1.7]">
        <div className="space-y-px">
          {visible.map((line, i) =>
            line.type === "spacer" ? (
              <div key={i} className="h-3" />
            ) : (
              <div
                key={i}
                className={cn(
                  line.type === "system" && "text-gray-500",
                  line.type === "agent" && "text-emerald-400/90",
                  line.type === "result" && "text-gray-300",
                  line.type === "success" && "text-green-400 font-medium",
                )}
              >
                {line.text}
              </div>
            ),
          )}
          {count < simulationLines.length && (
            <span className="inline-block h-3.5 w-[5px] translate-y-0.5 animate-pulse bg-emerald-400/70" />
          )}
        </div>
      </div>

      {/* Card footer */}
      <div className="flex items-center justify-between border-t border-white/[0.06] px-4 py-2.5">
        <span className="text-[10px] text-gray-600">payment-api \u00b7 us-east-1</span>
        <span className="text-[10px] text-gray-600">
          {count >= simulationLines.length ? "MTTR: 4m 12s" : "Live"}
        </span>
      </div>
    </div>
  )
}

// ── Features ──────────────────────────────────────────────────

const features = [
  {
    icon: Zap,
    title: "AI-Powered Triage",
    description:
      "Classifies severity, identifies affected services, and prioritizes incidents the moment they fire \u2014 no human bottleneck.",
    accent: "emerald",
    iconColor: "text-emerald-400",
    iconBg: "bg-emerald-500/10 border-emerald-500/20",
    visual: (
      <div className="mt-5 flex flex-col gap-2 rounded-lg border border-white/[0.04] bg-white/[0.02] p-3">
        {(["P1 Critical", "P2 High", "P3 Medium"] as const).map((label, i) => (
          <div key={label} className="flex items-center gap-3">
            <Badge
              className={cn(
                "w-20 justify-center text-[10px] leading-none py-0.5",
                i === 0 && "bg-red-600 text-white",
                i === 1 && "bg-orange-600 text-white",
                i === 2 && "bg-yellow-600 text-white",
              )}
            >
              {label}
            </Badge>
            <div className="h-1.5 flex-1 rounded-full bg-white/[0.06] overflow-hidden">
              <div
                className={cn(
                  "h-full rounded-full",
                  i === 0 && "w-[94%] bg-red-500/60",
                  i === 1 && "w-[4%] bg-orange-500/60",
                  i === 2 && "w-[2%] bg-yellow-500/60",
                )}
              />
            </div>
            <span className="w-8 text-right font-mono text-[10px] text-gray-500">
              {i === 0 ? "94%" : i === 1 ? "4%" : "2%"}
            </span>
          </div>
        ))}
      </div>
    ),
  },
  {
    icon: Radar,
    title: "Deep Investigation",
    description:
      "Maps the full blast radius across your stack and correlates logs, metrics, and traces to build a complete picture.",
    accent: "cyan",
    iconColor: "text-cyan-400",
    iconBg: "bg-cyan-500/10 border-cyan-500/20",
    visual: (
      <div className="mt-5 flex flex-col gap-1.5 rounded-lg border border-white/[0.04] bg-white/[0.02] p-3 font-mono text-[10px]">
        <div className="flex items-center gap-2">
          <span className="size-1.5 rounded-full bg-red-500" />
          <span className="text-gray-400">payment-api</span>
          <span className="ml-auto text-red-400">5,231 errors</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="size-1.5 rounded-full bg-yellow-500" />
          <span className="text-gray-400">checkout-svc</span>
          <span className="ml-auto text-yellow-400">847 timeouts</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="size-1.5 rounded-full bg-yellow-500" />
          <span className="text-gray-400">billing-worker</span>
          <span className="ml-auto text-yellow-400">queue backlog</span>
        </div>
      </div>
    ),
  },
  {
    icon: Crosshair,
    title: "Root Cause Analysis",
    description:
      "Pinpoints the root cause with confidence scoring and chains of evidence so you know exactly why it broke.",
    accent: "blue",
    iconColor: "text-blue-400",
    iconBg: "bg-blue-500/10 border-blue-500/20",
    visual: (
      <div className="mt-5 rounded-lg border border-white/[0.04] bg-white/[0.02] p-3">
        <div className="flex items-center justify-between">
          <span className="text-[10px] text-gray-500 uppercase tracking-wider">Confidence</span>
          <span className="font-mono text-xs font-medium text-blue-400">94%</span>
        </div>
        <div className="mt-2 h-1.5 w-full rounded-full bg-white/[0.06] overflow-hidden">
          <div className="h-full w-[94%] rounded-full bg-gradient-to-r from-blue-500 to-blue-400" />
        </div>
        <p className="mt-2.5 text-[10px] text-gray-500">
          Memory leak in payment-api v2.3.1 \u2014 introduced in commit a3f82d1
        </p>
      </div>
    ),
  },
  {
    icon: ShieldCheck,
    title: "Human-in-the-Loop",
    description:
      "Recommends ranked fix options with risk assessment. You approve, Parakeet executes \u2014 safely and traceably.",
    accent: "violet",
    iconColor: "text-violet-400",
    iconBg: "bg-violet-500/10 border-violet-500/20",
    visual: (
      <div className="mt-5 rounded-lg border border-white/[0.04] bg-white/[0.02] p-3">
        <div className="flex items-center justify-between">
          <span className="text-[11px] text-gray-300">Rollback to v2.3.0</span>
          <Badge className="bg-green-900/40 text-green-400 text-[10px] leading-none py-0.5 px-1.5">
            Low risk
          </Badge>
        </div>
        <div className="mt-3 flex gap-2">
          <div className="flex-1 rounded-md bg-emerald-500/20 py-1.5 text-center text-[10px] font-medium text-emerald-400 border border-emerald-500/30">
            Approve
          </div>
          <div className="flex-1 rounded-md bg-white/[0.04] py-1.5 text-center text-[10px] text-gray-500 border border-white/[0.06]">
            Reject
          </div>
        </div>
      </div>
    ),
  },
] as const

// ── Pipeline ──────────────────────────────────────────────────

const pipeline = [
  { icon: Bell, label: "Alert", desc: "Incident detected" },
  { icon: Layers, label: "Triage", desc: "Classify & prioritize" },
  { icon: Search, label: "Investigate", desc: "Map blast radius" },
  { icon: Crosshair, label: "Root Cause", desc: "Identify with evidence" },
  { icon: CheckCircle2, label: "Approve", desc: "Review & execute fix" },
  { icon: FileText, label: "Post-Mortem", desc: "Learn & improve" },
]

// ── Metrics ───────────────────────────────────────────────────

const metrics = [
  { value: "4.2 min", label: "Avg. resolution time", icon: Clock },
  { value: "94%", label: "Auto-triage accuracy", icon: Zap },
  { value: "6\u00d7", label: "Faster than manual", icon: TrendingDown },
  { value: "847", label: "Incidents resolved", icon: Activity },
]

// ── Background styles ─────────────────────────────────────────

const heroGlow = {
  background:
    "radial-gradient(ellipse 70% 50% at 50% -10%, rgba(16,185,129,0.10), transparent)",
} as const

const dotPattern = {
  backgroundImage:
    "radial-gradient(rgba(255,255,255,0.05) 1px, transparent 1px)",
  backgroundSize: "24px 24px",
} as const

const pipelineGlow = {
  background:
    "radial-gradient(ellipse 70% 50% at 50% 50%, rgba(16,185,129,0.04), transparent)",
} as const

const pipelineLine = {
  background:
    "linear-gradient(90deg, rgba(16,185,129,0) 0%, rgba(16,185,129,0.25) 10%, rgba(16,185,129,0.25) 90%, rgba(16,185,129,0) 100%)",
} as const

const novaGlow = {
  background:
    "radial-gradient(ellipse 60% 60% at 50% 40%, rgba(251,191,36,0.05), transparent)",
} as const

// ══════════════════════════════════════════════════════════════
// Landing Page
// ══════════════════════════════════════════════════════════════

export default function Landing() {
  return (
    <div className="min-h-screen bg-[#09090b] text-white selection:bg-emerald-500/20 overscroll-none">
      {/* ── Navigation ── */}
      <nav className="fixed top-0 z-50 w-full border-b border-white/[0.06] bg-[#09090b]/80 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
          <span className="flex items-center gap-2 text-lg font-semibold tracking-tight">
            <img src={parakeetLogo} alt="Parakeet" className="size-6 brightness-0 invert" />
            Parakeet
          </span>
          <div className="flex items-center gap-6">
            <a
              href="#features"
              className="hidden text-sm text-gray-500 transition-colors hover:text-gray-300 sm:block"
            >
              Features
            </a>
            <a
              href="#how-it-works"
              className="hidden text-sm text-gray-500 transition-colors hover:text-gray-300 sm:block"
            >
              How it works
            </a>
            <Button asChild size="sm" className="bg-emerald-600 text-white hover:bg-emerald-500">
              <Link to="/dashboard">Try the Demo</Link>
            </Button>
          </div>
        </div>
      </nav>

      <main>
        {/* ── Hero ── */}
        <section className="relative overflow-hidden px-6 pt-32 pb-20 lg:pt-40 lg:pb-28">
          <div className="pointer-events-none absolute inset-0" style={heroGlow} />
          <div className="pointer-events-none absolute inset-0 opacity-40" style={dotPattern} />

          <div className="relative z-10 mx-auto grid max-w-6xl items-center gap-12 lg:grid-cols-[1fr_420px] lg:gap-16">
            {/* Text */}
            <div>
              <div className="mb-8 inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/[0.07] px-4 py-1.5 text-sm text-emerald-400">
                <span className="size-1.5 animate-pulse rounded-full bg-emerald-400" />
                AI Incident Response Platform
              </div>

              <h1 className="text-5xl font-bold leading-[1.08] tracking-tight sm:text-6xl lg:text-7xl">
                <span className="bg-gradient-to-b from-white via-white to-white/50 bg-clip-text text-transparent">
                  Resolve incidents
                </span>
                <br />
                <span className="bg-gradient-to-b from-white via-white to-white/50 bg-clip-text text-transparent">
                  in minutes,
                </span>
                <br />
                <span className="bg-gradient-to-r from-emerald-400 to-emerald-300 bg-clip-text text-transparent">
                  not hours.
                </span>
              </h1>

              <p className="mt-8 max-w-lg text-lg leading-relaxed text-gray-400">
                AI agents that triage, investigate, and fix production incidents —
                with humans always in the loop.
              </p>

              <div className="mt-10 flex flex-wrap items-center gap-4">
                <Button asChild size="lg" className="bg-emerald-500 text-white shadow-lg shadow-emerald-500/20 hover:bg-emerald-400 hover:shadow-emerald-400/20">
                  <Link to="/dashboard">
                    Try the Demo
                    <ArrowRight className="size-4" />
                  </Link>
                </Button>
                <Button asChild variant="ghost" size="lg" className="text-gray-400 hover:text-white hover:bg-white/[0.04]">
                  <a href="#how-it-works">
                    See how it works
                    <ChevronRight className="size-4" />
                  </a>
                </Button>
              </div>
            </div>

            {/* Animated incident card */}
            <div className="hidden lg:block">
              <IncidentSimulation />
            </div>
          </div>
        </section>

        {/* ── Metrics ── */}
        <section className="border-y border-white/[0.06] px-6 py-12">
          <div className="mx-auto grid max-w-6xl grid-cols-2 gap-8 sm:grid-cols-4">
            {metrics.map((m) => (
              <div key={m.label} className="text-center">
                <m.icon className="mx-auto mb-3 size-5 text-emerald-400/60" />
                <div className="text-3xl font-bold tracking-tight">{m.value}</div>
                <div className="mt-1 text-sm text-gray-500">{m.label}</div>
              </div>
            ))}
          </div>
        </section>

        {/* ── Features ── */}
        <section id="features" className="relative px-6 py-28">
          <div className="mx-auto max-w-6xl">
            <div className="mb-16 text-center">
              <p className="mb-3 text-sm font-medium uppercase tracking-widest text-emerald-400/70">
                Capabilities
              </p>
              <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
                Intelligent at every stage
              </h2>
              <p className="mx-auto mt-4 max-w-2xl text-lg text-gray-400">
                Four AI agents work in concert to take an incident from alert to
                resolution — faster than any human team alone.
              </p>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              {features.map((f) => (
                <div
                  key={f.title}
                  className="group rounded-xl border border-white/[0.06] bg-white/[0.02] p-7 transition-all hover:border-white/[0.1] hover:bg-white/[0.04]"
                >
                  <div
                    className={cn(
                      "mb-5 inline-flex rounded-lg border p-2.5",
                      f.iconBg,
                    )}
                  >
                    <f.icon className={cn("size-5", f.iconColor)} />
                  </div>
                  <h3 className="text-lg font-semibold tracking-tight">
                    {f.title}
                  </h3>
                  <p className="mt-2 text-sm leading-relaxed text-gray-400">
                    {f.description}
                  </p>
                  {f.visual}
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── How It Works ── */}
        <section id="how-it-works" className="relative px-6 py-28">
          <div className="pointer-events-none absolute inset-0" style={pipelineGlow} />
          <div className="relative mx-auto max-w-5xl">
            <div className="mb-20 text-center">
              <p className="mb-3 text-sm font-medium uppercase tracking-widest text-emerald-400/70">
                Pipeline
              </p>
              <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
                From alert to resolution
              </h2>
              <p className="mx-auto mt-4 max-w-2xl text-lg text-gray-400">
                Every incident flows through a structured AI pipeline — automated
                where possible, human-controlled where it matters.
              </p>
            </div>

            {/* Desktop */}
            <div className="hidden lg:block">
              <div className="relative">
                <div
                  className="absolute left-[8%] right-[8%] top-[32px] h-px"
                  style={pipelineLine}
                />
                {Array.from({ length: pipeline.length - 1 }, (_, i) => (
                  <ChevronRight
                    key={i}
                    className="absolute z-[5] size-3 text-emerald-500/30"
                    style={{
                      top: "26px",
                      left: `${((i + 1) / pipeline.length) * 100}%`,
                      transform: "translateX(-50%)",
                    }}
                  />
                ))}
                <div className="relative z-10 grid grid-cols-6">
                  {pipeline.map((step, i) => (
                    <div key={step.label} className="flex flex-col items-center text-center">
                      <div className="rounded-2xl bg-[#09090b] p-1">
                        <div className="flex size-14 items-center justify-center rounded-xl border border-emerald-500/20 bg-emerald-500/[0.08]">
                          <step.icon className="size-5 text-emerald-400" />
                        </div>
                      </div>
                      <span className="mt-4 text-[10px] font-semibold uppercase tracking-widest text-emerald-400/40">
                        {String(i + 1).padStart(2, "0")}
                      </span>
                      <h4 className="mt-1.5 text-sm font-semibold tracking-tight">
                        {step.label}
                      </h4>
                      <p className="mt-1 text-xs leading-relaxed text-gray-500">
                        {step.desc}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Mobile */}
            <div className="lg:hidden">
              <div className="mx-auto max-w-xs">
                {pipeline.map((step, i) => (
                  <div key={step.label}>
                    <div className="flex items-center gap-4">
                      <div className="flex size-12 flex-shrink-0 items-center justify-center rounded-xl border border-emerald-500/20 bg-emerald-500/[0.08]">
                        <step.icon className="size-5 text-emerald-400" />
                      </div>
                      <div>
                        <h4 className="text-sm font-semibold">{step.label}</h4>
                        <p className="mt-0.5 text-xs text-gray-500">{step.desc}</p>
                      </div>
                    </div>
                    {i < pipeline.length - 1 && (
                      <div className="ml-6 flex h-6 items-center">
                        <div className="h-full w-px bg-emerald-500/20" />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* ── Amazon Nova ── */}
        <section className="px-6 py-28">
          <div className="mx-auto max-w-4xl">
            <div className="relative overflow-hidden rounded-2xl border border-white/[0.06] bg-white/[0.02] p-12 text-center sm:p-16">
              <div className="pointer-events-none absolute inset-0" style={novaGlow} />
              <div className="relative">
                <p className="mb-4 text-sm font-medium uppercase tracking-widest text-gray-500">
                  Powered by
                </p>
                <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
                  Built with{" "}
                  <span className="bg-gradient-to-r from-amber-300 to-orange-400 bg-clip-text text-transparent">
                    Amazon Nova
                  </span>
                </h2>
                <p className="mx-auto mt-6 max-w-xl text-lg leading-relaxed text-gray-400">
                  Amazon Nova 2 Lite is the reasoning engine powering every stage of
                  the Parakeet pipeline — from initial triage classification to root
                  cause analysis and remediation planning.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* ── Final CTA ── */}
        <section className="px-6 py-20">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
              Ready to resolve incidents faster?
            </h2>
            <p className="mx-auto mt-4 max-w-lg text-lg text-gray-400">
              See Parakeet in action. Explore the dashboard with simulated
              incidents and watch AI agents work through the pipeline.
            </p>
            <div className="mt-10">
              <Button asChild size="lg" className="bg-emerald-500 text-white shadow-lg shadow-emerald-500/20 hover:bg-emerald-400 hover:shadow-emerald-400/20">
                <Link to="/dashboard">
                  Try the Demo
                  <ArrowRight className="size-4" />
                </Link>
              </Button>
            </div>
          </div>
        </section>
      </main>

      {/* ── Footer ── */}
      <footer className="border-t border-white/[0.06] px-6 py-12">
        <div className="mx-auto flex max-w-6xl flex-col items-center gap-3 text-center">
          <span className="flex items-center gap-2 text-lg font-semibold tracking-tight">
            <img src={parakeetLogo} alt="Parakeet" className="size-6 brightness-0 invert" />
            Parakeet
          </span>
          <p className="text-sm text-gray-500">
            Built for the Amazon Nova AI Hackathon 2026.
          </p>
        </div>
      </footer>
    </div>
  )
}
