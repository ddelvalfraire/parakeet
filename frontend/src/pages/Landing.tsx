import { Link } from "react-router"

export default function Landing() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-background text-foreground">
      <h1 className="text-5xl font-bold tracking-tight">Parakeet</h1>
      <p className="mt-4 text-lg text-muted-foreground">
        Incident Response Management
      </p>
      <Link
        to="/dashboard"
        className="mt-8 inline-flex items-center justify-center rounded-md bg-primary px-6 py-3 text-sm font-medium text-primary-foreground shadow hover:bg-primary/90 transition-colors"
      >
        Go to Dashboard
      </Link>
    </div>
  )
}
