import { Link, Outlet } from "react-router"

export default function DashboardLayout() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b">
        <div className="container mx-auto flex h-14 items-center px-4">
          <Link to="/" className="text-lg font-semibold">
            Parakeet
          </Link>
          <nav className="ml-8 flex gap-4">
            <Link
              to="/dashboard"
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              Incidents
            </Link>
          </nav>
        </div>
      </header>
      <main className="container mx-auto px-4 py-8">
        <Outlet />
      </main>
    </div>
  )
}
