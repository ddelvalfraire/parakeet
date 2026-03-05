import { useParams } from "react-router"

export default function IncidentDetail() {
  const { id } = useParams<{ id: string }>()

  return (
    <div>
      <h1 className="text-3xl font-bold">Incident #{id}</h1>
      <p className="mt-2 text-muted-foreground">
        Full incident details and timeline.
      </p>
    </div>
  )
}
