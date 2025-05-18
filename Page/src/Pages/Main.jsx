import React from 'react'
import Layout from '../Layouts/Layout';
import backgroundImage from '../assets/images/map.png';

function Main() {
  return (
    <Layout>
      <header>
        <div className="container">
            <div className="logo">Guadalahacks 2025</div>
            <div className="tagline">Innovating for a better tomorrow in Zapopan, Jalisco</div>
            <a href="#demo" className="btn">See Our Project</a>
        </div>
    </header>
    
    <section id="about" className="hero">
        <div className="container">
            <div className="hero">
                <div className="hero-content">
                    <h1>Project Name</h1>
                    <p>Replace this with a concise description of your project. What problem does it solve? What makes it innovative? This should be a compelling introduction that captures the essence of your hackathon project in just a few sentences.</p>
                    <p>Explain why this project matters and how it was inspired by challenges observed during Guadalahacks.</p>
                    <div>
                        <a href="#features" className="btn">Key Features</a>
                        <a href="#demo" className="btn btn-secondary">View Demo</a>
                    </div>
                </div>
                <div className="hero-image">
                    <img src="/src/assets/images/map.png" alt="Project Screenshot" className="placeholder-img" />
                </div>
            </div>
        </div>
    </section>
    
    <section id="features" className="features">
        <div className="container">
            <h2>Key Features</h2>
            <div className="features-grid">
                <div className="feature-card">
                    <div className="feature-icon">🚀</div>
                    <h3>Feature 1</h3>
                    <p>Describe the first key feature of your project. What does it do? How does it solve a particular problem?</p>
                </div>
                <div className="feature-card">
                    <div className="feature-icon">⚡</div>
                    <h3>Feature 2</h3>
                    <p>Explain another core feature. Focus on benefits and innovation rather than technical details.</p>
                </div>
                <div className="feature-card">
                    <div className="feature-icon">🔒</div>
                    <h3>Feature 3</h3>
                    <p>Highlight a third key feature that makes your project stand out from others in the hackathon.</p>
                </div>
            </div>
        </div>
    </section>
    
    <section id="technology" className="timeline-section">
        <div className="container">
            <h2>Our Tech Stack</h2>
            <p className="text-center">The technologies we used to build this project during Guadalahacks:</p>
            
            <div className="timeline">
                <div className="timeline-item">
                    <div className="timeline-dot"></div>
                    <div className="timeline-content">
                        <span className="timeline-date">Frontend</span>
                        <h3>User Interface</h3>
                        <p>List the technologies you used for the frontend (e.g., React, Vue, Angular, etc.). Briefly explain why you chose these tools.</p>
                    </div>
                </div>
                
                <div className="timeline-item">
                    <div className="timeline-dot"></div>
                    <div className="timeline-content">
                        <span className="timeline-date">Backend</span>
                        <h3>Server & API</h3>
                        <p>Describe your backend technologies (e.g., Node.js, Django, Flask). What challenges did these help you overcome?</p>
                    </div>
                </div>
                
                <div className="timeline-item">
                    <div className="timeline-dot"></div>
                    <div className="timeline-content">
                        <span className="timeline-date">Database</span>
                        <h3>Data Storage</h3>
                        <p>Explain your database choice and why it was suitable for your project requirements.</p>
                    </div>
                </div>
                
                <div className="timeline-item">
                    <div className="timeline-dot"></div>
                    <div className="timeline-content">
                        <span className="timeline-date">Deployment</span>
                        <h3>Hosting & Infrastructure</h3>
                        <p>Share how you deployed your project and any DevOps tools or practices you implemented during the hackathon.</p>
                    </div>
                </div>
            </div>
        </div>
    </section>
    
    <section id="demo" className="demo">
        <div className="container">
            <h2>Project Demo</h2>
            <p>See our project in action. This demonstration showcases the key functionality we developed during Guadalahacks.</p>
            
            <div className="demo-video">
                <img src="/api/placeholder/800/450" alt="Project Demo" style={{width: '100%', height: 'auto'}} />
                {/* Replace with actual video or interactive demo */}
            </div>
            
            <a href="#" className="btn btn-accent">Try It Live</a>
        </div>
    </section>
    
    <section id="team" className="team">
        <div className="container">
            <h2>Our Team</h2>
            <p className="text-center">Meet the talented developers who built this project during Guadalahacks:</p>
            
            <div className="team-grid">
                <div className="team-member">
                    <img src="/api/placeholder/300/300" alt="Team Member 1" style={{width: '100%', height: 'auto'}} />
                    <div className="member-info">
                        <h3 className="member-name">Team Member 1</h3>
                        <div className="member-role">Frontend Developer</div>
                        <p>Brief description about this team member and their contribution to the project.</p>
                    </div>
                </div>
                
                <div className="team-member">
                    <img src="/api/placeholder/300/300" alt="Team Member 2" style={{width: '100%', height: 'auto'}} />
                    <div className="member-info">
                        <h3 className="member-name">Team Member 2</h3>
                        <div className="member-role">Backend Developer</div>
                        <p>Brief description about this team member and their contribution to the project.</p>
                    </div>
                </div>
                
                <div className="team-member">
                    <img src="/api/placeholder/300/300" alt="Team Member 3" style={{width: '100%', height: 'auto'}} />
                    <div className="member-info">
                        <h3 className="member-name">Team Member 3</h3>
                        <div className="member-role">UI/UX Designer</div>
                        <p>Brief description about this team member and their contribution to the project.</p>
                    </div>
                </div>
                
                <div className="team-member">
                    <img src="/api/placeholder/300/300" alt="Team Member 4" style={{width: '100%', height: 'auto'}} />
                    <div className="member-info">
                        <h3 className="member-name">Team Member 4</h3>
                        <div className="member-role">Data Scientist</div>
                        <p>Brief description about this team member and their contribution to the project.</p>
                    </div>
                </div>
            </div>
        </div>
    </section>
    
    <section id="challenges" className="features">
        <div className="container">
            <h2>Challenges & Learnings</h2>
            <div className="features-grid">
                <div className="feature-card">
                    <div className="feature-icon">🧩</div>
                    <h3>Problem We Faced</h3>
                    <p>Describe a significant challenge your team faced during the hackathon and how you overcame it.</p>
                </div>
                <div className="feature-card">
                    <div className="feature-icon">💡</div>
                    <h3>Our Solution</h3>
                    <p>Explain how you solved the problem with innovative thinking and teamwork.</p>
                </div>
                <div className="feature-card">
                    <div className="feature-icon">📈</div>
                    <h3>What We Learned</h3>
                    <p>Share key learnings and skills gained during Guadalahacks that will help your team in future projects.</p>
                </div>
            </div>
        </div>
    </section>
    
    <section id="future" className="hero">
        <div className="container">
            <div className="hero">
                <div className="hero-content">
                    <h2>Future Development</h2>
                    <p>If we had more time beyond the hackathon, here's how we would enhance our project:</p>
                    <ul style={{marginLeft: '2rem', marginBottom: '2rem'}}>
                        <li>Feature enhancement 1</li>
                        <li>Feature enhancement 2</li>
                        <li>Feature enhancement 3</li>
                        <li>Feature enhancement 4</li>
                    </ul>
                    <a href="#contact" className="btn">Get in Touch</a>
                </div>
                <div className="hero-image">
                    <img src="/api/placeholder/600/400" alt="Future Vision" className="placeholder-img" />
                </div>
            </div>
        </div>
    </section>
    
    <footer>
        <div className="container">
            <p>Created with ❤️ during Guadalahacks 2025 in Zapopan, Jalisco</p>
            
            <div className="social-links">
                <a href="#" className="social-icon">GH</a>
                <a href="#" className="social-icon">LI</a>
                <a href="#" className="social-icon">TW</a>
                <a href="#" className="social-icon">IG</a>
            </div>
            
            <p>&copy; 2025 Project Name. All rights reserved.</p>
        </div>
    </footer>
    </Layout>
  );
}

export default Main;
