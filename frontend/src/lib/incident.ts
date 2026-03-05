const timeFmt = new Intl.DateTimeFormat('en-US', {
  hour: '2-digit',
  minute: '2-digit',
  second: '2-digit',
  hour12: false,
})

const dateTimeFmt = new Intl.DateTimeFormat('en-US', {
  month: 'short',
  day: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
  hour12: false,
})

export function formatTime(iso: string): string {
  return timeFmt.format(new Date(iso))
}

export function formatDateTime(iso: string): string {
  return dateTimeFmt.format(new Date(iso))
}
