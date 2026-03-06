import { useEffect, useState } from 'react'
import { Link, Outlet, useLocation } from 'react-router'
import { api } from '@/api'
import { cn } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'
import parakeetLogo from '@/assets/Parakeet-logo.png'

export default function DashboardLayout() {
  const location = useLocation()
  const [activeCount, setActiveCount] = useState<number | null>(null)

  useEffect(() => {
    api
      .listIncidents()
      .then(res => {
        setActiveCount(
          res.incidents.filter(i => i.status !== 'resolved').length,
        )
      })
      .catch(() => {})
  }, [])

  const isIncidents =
    location.pathname === '/dashboard' ||
    location.pathname.startsWith('/incident')

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="sticky top-0 z-50 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto flex h-14 items-center px-4">
          <Link
            to="/"
            className="flex items-center gap-2 text-lg font-semibold tracking-tight"
          >
            <img src={parakeetLogo} alt="Parakeet" className="size-6" />
            Parakeet
          </Link>
          <nav className="ml-8 flex gap-4">
            <Link
              to="/dashboard"
              className={cn(
                'flex items-center gap-1.5 text-sm transition-colors',
                isIncidents
                  ? 'text-foreground font-medium'
                  : 'text-muted-foreground hover:text-foreground',
              )}
            >
              Incidents
              {activeCount !== null && activeCount > 0 && (
                <Badge className="h-5 min-w-5 bg-red-500 text-[10px] font-bold text-white hover:bg-red-500">
                  {activeCount}
                </Badge>
              )}
            </Link>
          </nav>
        </div>
      </header>
      <main className="container mx-auto px-4 py-6">
        <Outlet />
      </main>
    </div>
  )
}
