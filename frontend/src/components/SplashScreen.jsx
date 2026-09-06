import { useEffect, useState } from 'react'

export default function SplashScreen({ onDone }) {
  const [fading, setFading] = useState(false)

  useEffect(() => {
    const startFade = setTimeout(() => setFading(true), 1500)
    const finish = setTimeout(() => onDone(), 3100)
    return () => {
      clearTimeout(startFade)
      clearTimeout(finish)
    }
  }, [onDone])

  return (
    <div className={`splash-screen ${fading ? 'splash-fade-out' : ''}`}>
      <img src="/pixelnova-logo.png" alt="PIXELNOVA" className="splash-logo" />
    </div>
  )
}
