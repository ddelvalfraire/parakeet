import type { IncidentStatus, Severity, RiskLevel, ServiceStatus } from "@/types/domain"

// ---------------------------------------------------------------------------
// Severity — bold filled backgrounds (urgency-forward)
// ---------------------------------------------------------------------------

export interface SeverityStyle {
  label: string
  badge: string
  text: string
  border: string
  dot: string
}

export const severityConfig: Record<Severity, SeverityStyle> = {
  P1: {
    label: "Critical",
    badge: "bg-red-600 text-white dark:bg-red-500",
    text: "text-red-600 dark:text-red-400",
    border: "border-red-600 dark:border-red-500",
    dot: "bg-red-600 dark:bg-red-500",
  },
  P2: {
    label: "High",
    badge: "bg-orange-600 text-white dark:bg-orange-500",
    text: "text-orange-600 dark:text-orange-400",
    border: "border-orange-600 dark:border-orange-500",
    dot: "bg-orange-600 dark:bg-orange-500",
  },
  P3: {
    label: "Medium",
    badge: "bg-yellow-600 text-white dark:bg-yellow-500",
    text: "text-yellow-600 dark:text-yellow-400",
    border: "border-yellow-600 dark:border-yellow-500",
    dot: "bg-yellow-600 dark:bg-yellow-500",
  },
  P4: {
    label: "Low",
    badge: "bg-blue-600 text-white dark:bg-blue-500",
    text: "text-blue-600 dark:text-blue-400",
    border: "border-blue-600 dark:border-blue-500",
    dot: "bg-blue-600 dark:bg-blue-500",
  },
}

// ---------------------------------------------------------------------------
// Status — soft muted tints (scannable workflow state)
// ---------------------------------------------------------------------------

export interface StatusStyle {
  label: string
  badge: string
  icon: string
  dot: string
  animate: boolean
}

export const statusConfig: Record<IncidentStatus, StatusStyle> = {
  triaging: {
    label: "Triaging",
    badge: "bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-300",
    icon: "text-purple-600 dark:text-purple-400",
    dot: "bg-purple-600 dark:bg-purple-400",
    animate: true,
  },
  investigating: {
    label: "Investigating",
    badge: "bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300",
    icon: "text-blue-600 dark:text-blue-400",
    dot: "bg-blue-600 dark:bg-blue-400",
    animate: true,
  },
  root_cause: {
    label: "Root Cause",
    badge: "bg-indigo-100 text-indigo-800 dark:bg-indigo-900/40 dark:text-indigo-300",
    icon: "text-indigo-600 dark:text-indigo-400",
    dot: "bg-indigo-600 dark:bg-indigo-400",
    animate: true,
  },
  awaiting_approval: {
    label: "Awaiting Approval",
    badge: "bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300",
    icon: "text-amber-600 dark:text-amber-400",
    dot: "bg-amber-600 dark:bg-amber-400",
    animate: true,
  },
  resolving: {
    label: "Resolving",
    badge: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300",
    icon: "text-emerald-600 dark:text-emerald-400",
    dot: "bg-emerald-600 dark:bg-emerald-400",
    animate: true,
  },
  resolved: {
    label: "Resolved",
    badge: "bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300",
    icon: "text-green-600 dark:text-green-400",
    dot: "bg-green-600 dark:bg-green-400",
    animate: false,
  },
  error: {
    label: "Error",
    badge: "bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300",
    icon: "text-red-600 dark:text-red-400",
    dot: "bg-red-600 dark:bg-red-400",
    animate: false,
  },
  needs_input: {
    label: "Needs Input",
    badge: "bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300",
    icon: "text-amber-600 dark:text-amber-400",
    dot: "bg-amber-600 dark:bg-amber-400",
    animate: true,
  },
}

// ---------------------------------------------------------------------------
// Risk level — soft style
// ---------------------------------------------------------------------------

export interface RiskStyle {
  label: string
  badge: string
  text: string
  dot: string
}

export const riskConfig: Record<RiskLevel, RiskStyle> = {
  low: {
    label: "Low",
    badge: "bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300",
    text: "text-green-600 dark:text-green-400",
    dot: "bg-green-600 dark:bg-green-400",
  },
  medium: {
    label: "Medium",
    badge: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/40 dark:text-yellow-300",
    text: "text-yellow-600 dark:text-yellow-400",
    dot: "bg-yellow-600 dark:bg-yellow-400",
  },
  high: {
    label: "High",
    badge: "bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300",
    text: "text-red-600 dark:text-red-400",
    dot: "bg-red-600 dark:bg-red-400",
  },
}

// ---------------------------------------------------------------------------
// Service status — dot indicators
// ---------------------------------------------------------------------------

export interface ServiceStatusStyle {
  label: string
  badge: string
  text: string
  dot: string
  animate: boolean
}

export const serviceStatusConfig: Record<ServiceStatus, ServiceStatusStyle> = {
  down: {
    label: "Down",
    badge: "bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300",
    text: "text-red-600 dark:text-red-400",
    dot: "bg-red-600 dark:bg-red-400",
    animate: true,
  },
  degraded: {
    label: "Degraded",
    badge: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/40 dark:text-yellow-300",
    text: "text-yellow-600 dark:text-yellow-400",
    dot: "bg-yellow-600 dark:bg-yellow-400",
    animate: true,
  },
  healthy: {
    label: "Healthy",
    badge: "bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300",
    text: "text-green-600 dark:text-green-400",
    dot: "bg-green-600 dark:bg-green-400",
    animate: false,
  },
}

// ---------------------------------------------------------------------------
// Typography — consistent heading/body hierarchy
// ---------------------------------------------------------------------------

export const typography = {
  h1: "text-3xl font-bold tracking-tight",
  h2: "text-2xl font-semibold tracking-tight",
  h3: "text-xl font-semibold tracking-tight",
  h4: "text-lg font-semibold tracking-tight",
  body: "text-sm leading-relaxed",
  bodyLarge: "text-base leading-relaxed",
  caption: "text-xs text-muted-foreground",
  label: "text-sm font-medium",
  mono: "font-mono text-sm",
} as const

// ---------------------------------------------------------------------------
// Spacing — consistent page/section/card padding
// ---------------------------------------------------------------------------

export const spacing = {
  page: "px-6 py-6 lg:px-8",
  section: "space-y-6",
  card: "p-6",
  cardCompact: "p-4",
  stack: "space-y-4",
  stackTight: "space-y-2",
  stackLoose: "space-y-8",
  inline: "space-x-4",
  inlineTight: "space-x-2",
  inlineLoose: "space-x-6",
} as const

// ---------------------------------------------------------------------------
// Layout — common layout patterns
// ---------------------------------------------------------------------------

export const layout = {
  pageHeader: "flex items-center justify-between gap-4",
  cardGrid: "grid gap-4 sm:grid-cols-2 lg:grid-cols-3",
  cardGridWide: "grid gap-4 sm:grid-cols-2 lg:grid-cols-4",
  splitPanel: "grid gap-6 lg:grid-cols-[1fr_380px]",
  timeline: "relative space-y-4 pl-8 before:absolute before:left-3 before:top-2 before:h-[calc(100%-1rem)] before:w-px before:bg-border",
  centeredContent: "mx-auto max-w-5xl",
  centeredContentNarrow: "mx-auto max-w-3xl",
} as const
