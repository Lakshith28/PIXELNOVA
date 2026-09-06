export default function SatelliteHero() {
  return (
    <div className="hero-scene" aria-hidden="true">
      <div className="sun-flare" />

      <div className="earth-wrap">
        <div className="earth-atmosphere" />
        <div className="earth-globe">
          <div className="earth-continents" />
          <div className="earth-clouds" />
          <div className="earth-citylights" />
          <div className="earth-terminator" />
        </div>
      </div>

      <svg className="orbit-svg" viewBox="0 0 900 900" xmlns="http://www.w3.org/2000/svg">
        <path
          d="M 450 120 A 330 220 -18 1 1 449 120"
          fill="none"
          stroke="#7fb8d9"
          strokeWidth="1"
          strokeDasharray="3 7"
          opacity="0.35"
        />

        <g className="satellite-orbit-rig">
          <g transform="translate(-46 -14) rotate(-20)">
            <g transform="translate(-70 0)">
              <rect x="0" y="0" width="62" height="34" rx="2" fill="#16326b" stroke="#3a5583" strokeWidth="1.2" />
              <line x1="14" y1="0" x2="14" y2="34" stroke="#3a5583" strokeWidth="0.8" />
              <line x1="28" y1="0" x2="28" y2="34" stroke="#3a5583" strokeWidth="0.8" />
              <line x1="42" y1="0" x2="42" y2="34" stroke="#3a5583" strokeWidth="0.8" />
              <line x1="0" y1="17" x2="62" y2="17" stroke="#3a5583" strokeWidth="0.8" />
            </g>
            <g transform="translate(24 0)">
              <rect x="0" y="0" width="62" height="34" rx="2" fill="#16326b" stroke="#3a5583" strokeWidth="1.2" />
              <line x1="14" y1="0" x2="14" y2="34" stroke="#3a5583" strokeWidth="0.8" />
              <line x1="28" y1="0" x2="28" y2="34" stroke="#3a5583" strokeWidth="0.8" />
              <line x1="42" y1="0" x2="42" y2="34" stroke="#3a5583" strokeWidth="0.8" />
              <line x1="0" y1="17" x2="62" y2="17" stroke="#3a5583" strokeWidth="0.8" />
            </g>
            <line x1="-24" y1="9" x2="0" y2="9" stroke="#c9a24b" strokeWidth="2.5" />
            <line x1="24" y1="9" x2="48" y2="9" stroke="#c9a24b" strokeWidth="2.5" />
            <rect x="-24" y="-13" width="48" height="44" rx="5" fill="#caa24d" stroke="#8a6d2e" strokeWidth="1.5" />
            <rect x="-14" y="-4" width="28" height="18" rx="2" fill="#e9c877" stroke="#8a6d2e" strokeWidth="0.8" />
            <line x1="0" y1="-13" x2="0" y2="-30" stroke="#c9a24b" strokeWidth="1.5" />
            <circle cx="0" cy="-30" r="3" fill="#f2a65a" />
          </g>
        </g>
      </svg>

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
    </div>
  )
}
