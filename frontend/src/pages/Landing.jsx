import { Link } from 'react-router-dom'
import SatelliteHero from '../components/SatelliteHero'
import './landing.css'

const PIPELINE = [
  {
    title: 'Upload',
    body: 'Bring in a georeferenced Sentinel-2 scene. We check it belongs before anything else runs.',
  },
  {
    title: 'Validate',
    body: 'CRS, bands, resolution, cloud and no-data coverage — every scene is screened before it reaches the model.',
  },
  {
    title: 'Reconstruct',
    body: 'An AI super-resolution model rebuilds spatial detail from 10 m data toward a sub-4 m target.',
  },
  {
    title: 'Verify',
    body: 'Spectral and spatial consistency checks catch reconstructions that drift from what the satellite actually saw.',
  },
  {
    title: 'Decide',
    body: 'Confidence maps, extracted features, and change layers — ready for GIS, not just a sharper picture.',
  },
]

export default function Landing() {
  return (
    <div className="landing">
      <section className="hero">
        <div className="hero-copy">
          <p className="hero-kicker">Sentinel-2, reconstructed</p>
          <h1>
            See more in every
            <br />
            satellite pixel
          </h1>
          <p className="hero-subhead">
            PIXELNOVEL takes 10 metre Sentinel-2 imagery and reconstructs
            sub-4 metre spatial detail using AI — then tells you exactly
            where that detail can be trusted.
          </p>
          <Link to="/app" className="cta-button">
            Launch the platform
          </Link>
        </div>
        <SatelliteHero />
      </section>

      <section className="mission">
        <div className="mission-text">
          <h2>Sentinel-2 sees everywhere. It just can't see small.</h2>
          <p>
            At 10 metres per pixel, a narrow road, a small field boundary,
            or a newly built structure gets blended into its surroundings.
            The satellite still passed overhead and recorded something —
            the detail is just diluted across too few pixels to read
            clearly.
          </p>
          <p>
            Sharpening the image with AI is the easy part. Knowing which
            sharpened pixels to actually believe is the part that makes
            the result usable for real decisions.
          </p>
        </div>
        <div className="mission-accent" aria-hidden="true" />
      </section>

      <section className="pipeline">
        <h2>One upload, five stages</h2>
        <ol className="pipeline-list">
          {PIPELINE.map((stage, i) => (
            <li key={stage.title} className="pipeline-item">
              <span className="pipeline-index">{String(i + 1).padStart(2, '0')}</span>
              <div>
                <h3>{stage.title}</h3>
                <p>{stage.body}</p>
              </div>
            </li>
          ))}
        </ol>
      </section>

      <section className="honesty">
        <p className="honesty-quote">
          We cannot create information a satellite never observed. But we
          can use AI to reconstruct useful spatial detail from what it did
          observe — and quantify where that reconstruction can be
          trusted.
        </p>
        <p className="honesty-attribution">
          This is why every enhanced scene ships with a confidence layer,
          not just a sharper image.
        </p>
      </section>

      <section className="final-cta">
        <h2>Upload a scene and see it for yourself.</h2>
        <Link to="/app" className="cta-button">
          Launch the platform
        </Link>
      </section>
    </div>
  )
}
