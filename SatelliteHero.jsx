export default function SatelliteHero() {
  return (
    <svg
      className="hero-illustration"
      viewBox="0 0 900 560"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <defs>
        <radialGradient id="atmosphere" cx="50%" cy="100%" r="75%">
          <stop offset="0%" stopColor="#f2a65a" stopOpacity="0.55" />
          <stop offset="35%" stopColor="#c97b3f" stopOpacity="0.25" />
          <stop offset="100%" stopColor="#0b1830" stopOpacity="0" />
        </radialGradient>
        <linearGradient id="earthLimb" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#f2a65a" />
          <stop offset="18%" stopColor="#7a5a63" />
          <stop offset="55%" stopColor="#1c2a4a" />
          <stop offset="100%" stopColor="#0b1128" />
        </linearGradient>
        <linearGradient id="panelGradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#1a2b52" />
          <stop offset="100%" stopColor="#0d1730" />
        </linearGradient>
      </defs>

      {/* atmosphere glow */}
      <ellipse cx="450" cy="620" rx="520" ry="260" fill="url(#atmosphere)" />

      {/* earth limb arc */}
      <path
        d="M -50 560 C 150 380, 750 380, 950 560 L 950 620 L -50 620 Z"
        fill="url(#earthLimb)"
      />
      <path
        d="M -50 560 C 150 380, 750 380, 950 560"
        fill="none"
        stroke="#f2a65a"
        strokeWidth="2"
        strokeOpacity="0.6"
      />

      {/* orbit path */}
      <path
        className="orbit-path"
        d="M 120 300 C 260 150, 640 150, 780 300"
        fill="none"
        stroke="#4c6a94"
        strokeWidth="1.5"
        strokeDasharray="4 8"
        opacity="0.5"
      />

      {/* satellite rig: this group is what animates upward on load */}
      <g className="satellite-rig">
        <g transform="translate(450 235) rotate(-8)">
          {/* left solar panel */}
          <g transform="translate(-150 -14)">
            <rect x="0" y="0" width="110" height="60" rx="3" fill="url(#panelGradient)" stroke="#3a5583" strokeWidth="1.5" />
            {[1, 2, 3, 4].map((i) => (
              <line key={i} x1={i * 22} y1="0" x2={i * 22} y2="60" stroke="#3a5583" strokeWidth="1" />
            ))}
            <line x1="0" y1="30" x2="110" y2="30" stroke="#3a5583" strokeWidth="1" />
          </g>
          {/* right solar panel */}
          <g transform="translate(40 -14)">
            <rect x="0" y="0" width="110" height="60" rx="3" fill="url(#panelGradient)" stroke="#3a5583" strokeWidth="1.5" />
            {[1, 2, 3, 4].map((i) => (
              <line key={i} x1={i * 22} y1="0" x2={i * 22} y2="60" stroke="#3a5583" strokeWidth="1" />
            ))}
            <line x1="0" y1="30" x2="110" y2="30" stroke="#3a5583" strokeWidth="1" />
          </g>
          {/* connecting struts */}
          <line x1="-40" y1="16" x2="0" y2="16" stroke="#5b7bab" strokeWidth="3" />
          <line x1="40" y1="16" x2="80" y2="16" stroke="#5b7bab" strokeWidth="3" />
          {/* body */}
          <rect x="-40" y="-22" width="80" height="76" rx="8" fill="#0d1730" stroke="#5b7bab" strokeWidth="2" />
          <rect x="-24" y="-10" width="48" height="30" rx="4" fill="#132248" stroke="#3a5583" strokeWidth="1" />
          {/* antenna */}
          <line x1="0" y1="-22" x2="0" y2="-52" stroke="#5b7bab" strokeWidth="2" />
          <circle cx="0" cy="-52" r="5" fill="#f2a65a" />
        </g>
      </g>

      {/* stars */}
      {[
        [60, 80], [140, 40], [230, 110], [320, 30], [400, 90],
        [520, 50], [610, 100], [700, 40], [800, 90], [850, 150],
        [30, 200], [180, 180], [860, 250], [780, 200], [500, 20],
      ].map(([x, y], i) => (
        <circle key={i} cx={x} cy={y} r={i % 3 === 0 ? 1.6 : 1} fill="#cfe0f5" opacity={i % 2 === 0 ? 0.8 : 0.4} />
      ))}
    </svg>
  )
}
