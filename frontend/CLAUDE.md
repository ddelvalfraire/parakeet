# Parakeet Frontend — Agent Design System Guide

## Design Identity

Parakeet is a professional incident management tool — clean, confident, information-dense.

- **Color communicates meaning.** The chrome is neutral. Color appears only for severity, status, and health indicators.
- **Density is a feature.** Operators need to scan many incidents quickly. Prioritize scannable layouts: tight tables, compact cards, clear hierarchy.
- **Filled icons over outlined.** Bigger shapes with color fill are easier to scan at small sizes, especially in tables and badges.
- **Progressive disclosure.** Show essentials at rest (severity, title, status, time), reveal detail on hover or click.
- **Smart hover states.** Cards and rows should subtly elevate or highlight on hover, inviting interaction without being distracting.

---

## Technical Rules

1. **Always use shadcn components** — never raw HTML for buttons, inputs, tables, dialogs, etc. All shadcn components live in `src/components/ui/`.
2. **Always use design tokens from `@/lib/styles`** — never hardcode severity colors, status labels, or spacing values.
3. **Use `cn()` from `@/lib/utils` for class merging** — never template literals for conditional Tailwind classes.
4. **Use CVA (`class-variance-authority`) for component variants** — any component with size/color/state variants.
5. **Icons from `lucide-react` only** — standard `size-4` for inline, `size-5` for standalone. Prefer filled variants where available.
6. **Typography from `typography` constants** — import from `@/lib/styles` for consistent heading/body hierarchy.
7. **Spacing from `spacing` constants** — import from `@/lib/styles` for consistent page/section/card padding.
8. **Layout from `layout` constants** — import from `@/lib/styles` for common layout patterns (page headers, card grids, split panels, timelines).
9. **Custom components go in `src/components/`** — never modify files in `src/components/ui/`.
10. **Toasts via `toast()` from `sonner`** — Toaster is already mounted in App.tsx. Just import `toast` from `sonner` and call it.
11. **Dark mode**: all custom colors must work in both light and dark modes. The design tokens in `@/lib/styles` already handle this with `dark:` variants.
12. **Domain types** live in `src/types/`. Always import `Severity`, `IncidentStatus`, `RiskLevel`, `ServiceStatus` etc. from there.

---

## Code Patterns

### Severity Badge

```tsx
import { Badge } from "@/components/ui/badge"
import { severityConfig } from "@/lib/styles"
import { cn } from "@/lib/utils"
import type { Severity } from "@/types/domain"

function SeverityBadge({ severity }: { severity: Severity }) {
  const config = severityConfig[severity]
  return (
    <Badge className={cn("font-semibold", config.badge)}>
      {severity} — {config.label}
    </Badge>
  )
}
```

### Status Badge with Animated Dot

```tsx
import { Badge } from "@/components/ui/badge"
import { statusConfig } from "@/lib/styles"
import { cn } from "@/lib/utils"
import type { IncidentStatus } from "@/types/domain"

function StatusBadge({ status }: { status: IncidentStatus }) {
  const config = statusConfig[status]
  return (
    <Badge variant="secondary" className={cn("gap-1.5", config.badge)}>
      <span
        className={cn(
          "inline-block size-2 rounded-full",
          config.dot,
          config.animate && "animate-pulse"
        )}
      />
      {config.label}
    </Badge>
  )
}
```

### Page Layout Skeleton

```tsx
import { typography, spacing, layout } from "@/lib/styles"

function MyPage() {
  return (
    <div className={spacing.page}>
      <div className={layout.pageHeader}>
        <h1 className={typography.h1}>Page Title</h1>
        {/* action buttons */}
      </div>
      <div className={spacing.section}>
        {/* page content */}
      </div>
    </div>
  )
}
```

### Card with Hover State

```tsx
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { spacing } from "@/lib/styles"

function IncidentCard() {
  return (
    <Card className="transition-colors hover:bg-accent/50 cursor-pointer">
      <CardHeader className={spacing.cardCompact}>
        <CardTitle className="text-sm font-medium">
          {/* title */}
        </CardTitle>
      </CardHeader>
      <CardContent className={spacing.cardCompact}>
        {/* content */}
      </CardContent>
    </Card>
  )
}
```

### Table Row Pattern

```tsx
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

function IncidentTable() {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="w-20">Severity</TableHead>
          <TableHead>Summary</TableHead>
          <TableHead className="w-32">Status</TableHead>
          <TableHead className="w-40 text-right">Updated</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <TableRow className="cursor-pointer hover:bg-accent/50">
          <TableCell>{/* SeverityBadge */}</TableCell>
          <TableCell className="font-medium">{/* summary */}</TableCell>
          <TableCell>{/* StatusBadge */}</TableCell>
          <TableCell className="text-right text-muted-foreground">
            {/* relative time */}
          </TableCell>
        </TableRow>
      </TableBody>
    </Table>
  )
}
```

---

## Project Structure

```
src/
  components/
    ui/          ← shadcn components (DO NOT MODIFY)
    ...          ← custom components go here
  hooks/         ← custom hooks
  layouts/       ← page layout wrappers
  lib/
    styles.ts    ← design tokens (severity, status, typography, spacing, layout)
    utils.ts     ← cn() utility
  pages/         ← route page components
  types/         ← domain types (Severity, IncidentStatus, etc.)
```

## Stack

- **React 19** + **React Router 7** (SPA mode)
- **Tailwind CSS 4** (via Vite plugin)
- **shadcn/ui** (new-york style, neutral base)
- **Radix UI** (headless primitives, via shadcn)
- **Lucide React** (icons)
- **CVA** (class-variance-authority for component variants)
- **Sonner** (toast notifications)
- **next-themes** (dark mode via ThemeProvider in App.tsx)
