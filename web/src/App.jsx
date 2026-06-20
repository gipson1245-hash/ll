import { useState, useEffect } from 'react'
import './App.css'
import heroImage from './assets/zeroops-hero-wide.png'
import logoImage from './assets/zeroops-social.png'

function App() {
  const [news, setNews] = useState([])
  const [email, setEmail] = useState('')

  useEffect(() => {
    fetch('/news.json')
      .then(res => res.json())
      .then(data => setNews(data))
      .catch(err => console.error("No news found yet", err))
  }, [])

  return (
    <div className="container">
      <header>
        <img src={logoImage} alt="ZeroOps Logo" className="logo" />
        <h1>ZeroOps Media</h1>
        <p className="subtitle">Zero Friction, Zero Fluff. Your Automated Intelligence Briefing.</p>
      </header>

      <main>
        <section className="hero">
          <img src={heroImage} alt="ZeroOps Media Hero" className="hero-img" />
          <h2>Stay Ahead in AI-Powered SMB Automation</h2>
          <p>We curate the most important news, tools, and workflow hacks for busy professionals. All delivered automatically to your inbox.</p>
          
          <form 
            action="https://buttondown.email/api/emails/embed-subscribe/zeroops" 
            method="post" 
            target="popupwindow" 
            className="subscribe-form"
          >
            <input 
              type="email" 
              name="email" 
              placeholder="Enter your email" 
              required 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            <input type="hidden" value="1" name="embed" />
            <button type="submit">Get the Intelligence</button>
          </form>
          <p className="small">Join 100+ professionals staying competitive with ZeroOps.</p>
        </section>

        <section className="latest-news">
          <h2>Latest Updates</h2>
          {news.length > 0 ? (
            <div className="news-grid">
              {news.map((item, index) => (
                <div key={index} className="news-card">
                  <h3>{item.title}</h3>
                  <p>{item.summary}</p>
                  <a href={item.link} target="_blank" rel="noopener noreferrer">Read More</a>
                </div>
              ))}
            </div>
          ) : (
            <p>Scanning the horizon for new intelligence...</p>
          )}
        </section>
      </main>

      <footer>
        <p>&copy; 2026 ZeroOps Media. Operating with near-zero manual oversight.</p>
      </footer>
    </div>
  )
}

export default App
