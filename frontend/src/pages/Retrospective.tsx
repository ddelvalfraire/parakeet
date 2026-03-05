import { useParams } from "react-router"

export default function Retrospective() {
  const { id } = useParams<{ id: string }>()

  return (
    <div>
      <h1 className="text-3xl font-bold">Retrospective — Incident #{id}</h1>
      <p className="mt-2 text-muted-foreground">
        Post-mortem analysis and references.
      </p>
    </div>
  )
}
