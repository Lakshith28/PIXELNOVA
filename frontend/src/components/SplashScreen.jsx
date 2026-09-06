import { useEffect, useState } from 'react'

export default function SplashScreen({ onDone }) {
  const [fading, setFading] = useState(false)

  useEffect(() => {
    const startFade = setTimeout(() => setFading(true), 1200)
    const finish = setTimeout(() => onDone(), 2000)
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
