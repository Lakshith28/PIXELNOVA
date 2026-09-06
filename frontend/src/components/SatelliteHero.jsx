export default function SatelliteHero() {
  return (
    <div className="hero-scene" aria-hidden="true">
      <svg className="stars-svg" viewBox="0 0 900 900" xmlns="http://www.w3.org/2000/svg">
        {[
          [60, 80], [140, 40], [230, 700], [320, 30], [780, 90],
          [520, 50], [610, 780], [700, 40], [800, 690], [850, 150],
          [30, 400], [180, 780], [860, 250], [40, 650], [500, 20],
          [760, 500], [90, 250], [650, 60], [400, 800], [830, 400],
        ].map(([x, y], i) => (
          <circle key={i} cx={x} cy={y} r={i % 3 === 0 ? 1.6 : 1} fill="#cfe0f5" opacity={i % 2 === 0 ? 0.8 : 0.4} />
        ))}
      </svg>

      <div className="orbit-stage">
        <div className="earth-atmosphere" />
        <div className="earth-globe">
          <div className="earth-terminator" />
        </div>

        <svg className="orbit-svg" viewBox="0 0 900 900" xmlns="http://www.w3.org/2000/svg">
          <path
            d="M 817 352 A 380 260 -15 1 1 83 548 A 380 260 -15 1 1 817 352"
            fill="none"
            stroke="#7fb8d9"
            strokeWidth="1.2"
            strokeDasharray="3 7"
            opacity="0.4"
          />
        </svg>

        <div className="satellite-orbit-rig">
          <svg className="satellite-svg" viewBox="-70 -60 140 120" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="goldFoil" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#f3d38a" />
                <stop offset="45%" stopColor="#caa24d" />
                <stop offset="100%" stopColor="#8a6d2e" />
              </linearGradient>
              <linearGradient id="panelBlue" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#2c4d8a" />
                <stop offset="100%" stopColor="#0e2040" />
              </linearGradient>
            </defs>

            <g transform="rotate(-15)">
              <g transform="translate(-118 -20)">
                <rect x="0" y="0" width="94" height="42" rx="1.5" fill="url(#panelBlue)" stroke="#9ec3ec" strokeWidth="1" />
                {[1, 2, 3, 4, 5].map((i) => (
                  <line key={`l-${i}`} x1={i * 15.6} y1="0" x2={i * 15.6} y2="42" stroke="#4d6ea3" strokeWidth="0.6" />
                ))}
                <line x1="0" y1="21" x2="94" y2="21" stroke="#4d6ea3" strokeWidth="0.6" />
              </g>
              <g transform="translate(24 -20)">
                <rect x="0" y="0" width="94" height="42" rx="1.5" fill="url(#panelBlue)" stroke="#9ec3ec" strokeWidth="1" />
                {[1, 2, 3, 4, 5].map((i) => (
                  <line key={`r-${i}`} x1={i * 15.6} y1="0" x2={i * 15.6} y2="42" stroke="#4d6ea3" strokeWidth="0.6" />
                ))}
                <line x1="0" y1="21" x2="94" y2="21" stroke="#4d6ea3" strokeWidth="0.6" />
              </g>
              <line x1="-24" y1="1" x2="0" y2="1" stroke="#d9d9d9" strokeWidth="2.5" />
              <line x1="24" y1="1" x2="48" y2="1" stroke="#d9d9d9" strokeWidth="2.5" />

              <rect x="-24" y="-24" width="48" height="50" rx="4" fill="url(#goldFoil)" stroke="#6b5322" strokeWidth="1.2" />
              <rect x="-24" y="-24" width="48" height="50" rx="4" fill="none" stroke="#fff3d1" strokeWidth="0.5" opacity="0.4" />
              {[-16, -8, 0, 8, 16].map((y, i) => (
                <line key={i} x1="-22" y1={y} x2="22" y2={y + 3} stroke="#6b5322" strokeWidth="0.4" opacity="0.5" />
              ))}
              <rect x="-13" y="-10" width="26" height="20" rx="2" fill="#182642" stroke="#0a1428" strokeWidth="1" />
              <circle cx="0" cy="0" r="5" fill="#0a1428" stroke="#3a5583" strokeWidth="1" />

              <g transform="translate(0 -24)">
                <ellipse cx="0" cy="-8" rx="10" ry="5" fill="#d8d8d8" stroke="#8a8a8a" strokeWidth="1" />
                <line x1="0" y1="-3" x2="0" y2="0" stroke="#9ec3ec" strokeWidth="1.5" />
              </g>
              <line x1="14" y1="-24" x2="20" y2="-38" stroke="#d8d8d8" strokeWidth="1.2" />
              <circle cx="20" cy="-38" r="2" fill="#f2a65a" />
            </g>
          </svg>
        </div>
      </div>
    </div>
  )
}
