document.addEventListener('DOMContentLoaded', () => {
    // -------------------------------------------------------------
    // Custom Geometric Cursor
    // -------------------------------------------------------------
    const cursor = document.getElementById('custom-cursor');
    const cursorFollower = document.getElementById('custom-cursor-follower');
    
    let mouseX = 0, mouseY = 0;
    let followerX = 0, followerY = 0;

    document.addEventListener('mousemove', (e) => {
        mouseX = e.clientX;
        mouseY = e.clientY;
        
        cursor.style.left = `${mouseX}px`;
        cursor.style.top = `${mouseY}px`;
    });

    // Smooth follower loop
    function animateFollower() {
        const easing = 0.15;
        followerX += (mouseX - followerX) * easing;
        followerY += (mouseY - followerY) * easing;
        cursorFollower.style.transform = `translate(calc(-50% + ${followerX}px), calc(-50% + ${followerY}px))`;
        requestAnimationFrame(animateFollower);
    }
    animateFollower();

    // Hover effects for interactive elements
    const interactives = document.querySelectorAll('a, button, .glass-card, .contact-link');
    interactives.forEach(el => {
        el.addEventListener('mouseenter', () => document.body.classList.add('hovering'));
        el.addEventListener('mouseleave', () => document.body.classList.remove('hovering'));
    });

    // -------------------------------------------------------------
    // Typewriter Effect
    // -------------------------------------------------------------
    const typewriterText = "Software Engineer";
    const typewriterElement = document.getElementById('typewriter-text');
    let typeIndex = 0;
    let isDeleting = false;

    function typeWriter() {
        if (!typewriterElement) return;
        const currentText = typewriterElement.textContent;
        
        if (!isDeleting && typeIndex < typewriterText.length) {
            typewriterElement.textContent += typewriterText.charAt(typeIndex);
            typeIndex++;
            setTimeout(typeWriter, 100);
        } else if (isDeleting && typeIndex > 0) {
            typewriterElement.textContent = typewriterText.substring(0, typeIndex - 1);
            typeIndex--;
            setTimeout(typeWriter, 50);
        } else {
            isDeleting = !isDeleting;
            setTimeout(typeWriter, isDeleting ? 2500 : 800); 
        }
    }
    setTimeout(typeWriter, 1000);

    // -------------------------------------------------------------
    // Scroll Animations (Intersection Observer)
    // -------------------------------------------------------------
    const fadeElements = document.querySelectorAll('.fade-in');
    const observerOptions = { root: null, rootMargin: '0px', threshold: 0.15 };
    const observer = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) { entry.target.classList.add('visible'); } 
            else { entry.target.classList.remove('visible'); }
        });
    }, observerOptions);
    fadeElements.forEach(el => observer.observe(el));

    // Navbar Scrolled State
    const nav = document.querySelector('.glass-nav');
    if (nav) {
        window.addEventListener('scroll', () => {
            if (window.scrollY > 50) { nav.classList.add('scrolled'); } 
            else { nav.classList.remove('scrolled'); }
        });
    }

    // -------------------------------------------------------------
    // Interactive NASA Space Engine
    // -------------------------------------------------------------
    const canvas = document.getElementById('particle-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    
    let hw = canvas.width = window.innerWidth;
    let hh = canvas.height = window.innerHeight;

    window.addEventListener('resize', () => {
        hw = canvas.width = window.innerWidth;
        hh = canvas.height = window.innerHeight;
    });

    const mouse = { x: hw / 2, y: hh / 2 };
    window.addEventListener('mousemove', (e) => {
        mouse.x = e.clientX;
        mouse.y = e.clientY;
    });

    // 3D Engine Variables
    let stars = [];
    let planets = [];
    let ships = [];
    const fov = 500;
    
    let camX = 0, camY = 0, camZ = -500;
    let baseTargetCamX = 0, baseTargetCamY = 0, baseTargetCamZ = -500;

    let time = 0;
    let scrollProgress = 0;

    window.addEventListener('scroll', () => {
        scrollProgress = window.scrollY / (document.body.scrollHeight - window.innerHeight);
        if (isNaN(scrollProgress) || scrollProgress === Infinity || scrollProgress < 0) {
            scrollProgress = 0;
        }
    });

    function generateScene() {
        stars = []; planets = []; ships = [];
        const starColors = ['#ffffff', '#baccff', '#ffccaa', '#fff4e8', '#cce0ff'];
        for (let i = 0; i < 1500; i++) {
            stars.push({
                x: (Math.random() * 20000) - 10000,
                y: (Math.random() * 20000) - 10000,
                z: (Math.random() * 24000) - 6000,
                size: Math.random() * 2.5 + 0.5,
                color: starColors[Math.floor(Math.random() * starColors.length)]
            });
        }

        // We leave name empty for the Sun so it isn't "too loud" and blends dynamically with HTML text
        planets.push({
            name: "", type: "sun", orbitRadius: 0, orbitSpeed: 0, angle: 0,
            baseSize: 220, color1: "#ffffff", color2: "#ffd166", hasRing: false
        });
        planets.push({
            name: "About", type: "planet", orbitRadius: 2500, orbitSpeed: 0.0016, angle: Math.random() * Math.PI*2,
            baseSize: 140, color1: "#4361ee", color2: "#3f37c9", hasRing: false
        });
        planets.push({
            name: "Expertise", type: "planet", orbitRadius: 4000, orbitSpeed: 0.0013, angle: Math.random() * Math.PI*2,
            baseSize: 135, color1: "#8338ec", color2: "#3a0ca3", hasRing: true
        });
        planets.push({
            name: "Skills", type: "planet", orbitRadius: 5500, orbitSpeed: 0.0011, angle: Math.random() * Math.PI*2,
            baseSize: 150, color1: "#4cc9f0", color2: "#4895ef", hasRing: false
        });
        planets.push({
            name: "Projects", type: "planet", orbitRadius: 7500, orbitSpeed: 0.0009, angle: Math.random() * Math.PI*2,
            baseSize: 160, color1: "#f72585", color2: "#b5179e", hasRing: true
        });
        planets.push({
            name: "Education", type: "planet", orbitRadius: 10000, orbitSpeed: 0.0007, angle: Math.random() * Math.PI*2,
            baseSize: 130, color1: "#fdb833", color2: "#ff7a00", hasRing: false
        });
        planets.push({
            name: "Contact", type: "planet", orbitRadius: 13000, orbitSpeed: 0.0004, angle: Math.PI/4, 
            baseSize: 180, color1: "#2ec4b6", color2: "#011627", hasRing: true
        });

        for (let i = 0; i < 35; i++) {
            ships.push({
                x: (Math.random() - 0.5) * 15000, y: (Math.random() - 0.5) * 4000, z: (Math.random() * 15000),
                speedZ: Math.random() * 25 + 10, spreadX: (Math.random() - 0.5) * 6, spreadY: (Math.random() - 0.5) * 6,
                isComet: Math.random() > 0.5 
            });
        }
    }

    function animate3D() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        time += 0.01;

        let contactPlanet = planets[planets.length - 1]; 
        let cx = Math.cos(contactPlanet.angle) * contactPlanet.orbitRadius;
        let cz = Math.sin(contactPlanet.angle) * contactPlanet.orbitRadius;

        // Dynamic flight path capturing the complete orbital planes
        let startZ = -900, startX = 0;
        let endZ = cz - 800, endX = cx - 300; 

        baseTargetCamZ = startZ + (endZ - startZ) * scrollProgress;
        baseTargetCamX = startX + (endX - startX) * scrollProgress;
        baseTargetCamY = -scrollProgress * 2500; 
        
        let tiltX = scrollProgress * 0.4;
        let mParallaxX = (mouse.x - hw / 2) * 1.5;
        let mParallaxY = (mouse.y - hh / 2) * 1.5; 

        camX += (baseTargetCamX + mParallaxX - camX) * 0.05;
        camY += (baseTargetCamY + mParallaxY - camY) * 0.05;
        camZ += (baseTargetCamZ - camZ) * 0.05;

        // Draw Stars
        for (let s of stars) {
            let dx = s.x - camX, dy = s.y - camY, dz = s.z - camZ;
            if (dz > 10) {
                let scale = fov / dz;
                let screenX = hw/2 + dx*scale, screenY = hh/2 + dy*scale;
                if (screenX > -50 && screenX < hw+50 && screenY > -50 && screenY < hh+50) {
                    ctx.globalAlpha = Math.min(0.8, 1200/dz);
                    ctx.fillStyle = s.color;
                    ctx.beginPath(); ctx.arc(screenX, screenY, Math.max(0.5, s.size * scale), 0, Math.PI*2);
                    ctx.fill(); ctx.globalAlpha = 1.0;
                }
            }
        }

        // Draw Orbital Lines
        ctx.lineWidth = 1.5;
        for (let p of planets) {
            if (p.orbitRadius > 0) {
                ctx.beginPath();
                let first = true;
                for (let a = 0; a <= Math.PI*2 + 0.1; a += 0.1) {
                    let rx = Math.cos(a) * p.orbitRadius, rz = Math.sin(a) * p.orbitRadius, ry = 0;
                    let ty = ry * Math.cos(tiltX) - rz * Math.sin(tiltX);
                    let tz = ry * Math.sin(tiltX) + rz * Math.cos(tiltX);
                    let dx = rx - camX, dy = ty - camY, dz = tz - camZ;
                    if (dz > 10) {
                        let scale = fov/dz, sx = hw/2 + dx*scale, sy = hh/2 + dy*scale;
                        if (first) { ctx.moveTo(sx, sy); first = false; } else { ctx.lineTo(sx, sy); }
                    }
                }
                ctx.strokeStyle = `rgba(255, 255, 255, ${Math.max(0.05, 0.25 - scrollProgress*0.15)})`;
                ctx.stroke();
            }
        }

        // Draw Spaceships/Comets
        for (let ship of ships) {
            ship.z -= ship.speedZ; ship.x += ship.spreadX; ship.y += ship.spreadY;
            if (ship.z < camZ - 200) {
                ship.z = camZ + 15000; ship.x = camX + (Math.random() - 0.5) * 8000; ship.y = camY + (Math.random() - 0.5) * 8000;
            }
            let dx = ship.x - camX, dy = ship.y - camY, dz = ship.z - camZ;
            if (dz > 10) {
                let scale = fov / dz, screenX = hw/2 + dx*scale, screenY = hh/2 + dy*scale;
                if (screenX > -50 && screenX < hw+50 && screenY > -50 && screenY < hh+50) {
                    ctx.save(); ctx.translate(screenX, screenY);
                    ctx.rotate(Math.atan2(ship.spreadY, ship.spreadX));
                    let rScale = Math.max(0.1, scale * 3); ctx.scale(rScale, rScale);
                    if (ship.isComet) {
                        let grad = ctx.createLinearGradient(0, 0, -60, 0);
                        grad.addColorStop(0, 'rgba(255,255,255,1)'); grad.addColorStop(0.2, 'rgba(100,200,255,0.8)'); grad.addColorStop(1, 'rgba(0,0,0,0)');
                        ctx.beginPath(); ctx.arc(0, 0, 2, 0, Math.PI*2); ctx.fillStyle = '#ffffff'; ctx.fill();
                        ctx.beginPath(); ctx.moveTo(2,0); ctx.lineTo(-60,6); ctx.lineTo(-60,-6); ctx.fillStyle = grad; ctx.fill();
                    } else {
                        ctx.beginPath(); ctx.moveTo(12,0); ctx.lineTo(-8,8); ctx.lineTo(-4,0); ctx.lineTo(-8,-8); ctx.closePath();
                        ctx.fillStyle = '#ffffff'; ctx.fill();
                        ctx.beginPath(); ctx.arc(-8,0,5,0, Math.PI*2); ctx.fillStyle = 'rgba(0,255,255,0.8)'; ctx.fill();
                    }
                    ctx.restore();
                }
            }
        }

        // Draw Planets and Zero-gravity Flags
        for (let p of planets) {
            p.angle += p.orbitSpeed;
            let rx = Math.cos(p.angle) * p.orbitRadius, rz = Math.sin(p.angle) * p.orbitRadius, ry = 0;
            let ty = ry * Math.cos(tiltX) - rz * Math.sin(tiltX);
            let tz = ry * Math.sin(tiltX) + rz * Math.cos(tiltX);
            let dx = rx - camX, dy = ty - camY, dz = tz - camZ;

            if (dz > 10 && dz < 14000) { 
                let scale = fov / dz, screenX = hw / 2 + dx * scale, screenY = hh / 2 + dy * scale;
                let r = Math.max(1, p.baseSize * scale);

                ctx.beginPath(); ctx.arc(screenX, screenY, r, 0, Math.PI*2);
                if (p.type === 'sun') {
                    let grad = ctx.createRadialGradient(screenX, screenY, 0, screenX, screenY, r * 3);
                    grad.addColorStop(0, '#ffffff'); grad.addColorStop(0.15, p.color2); grad.addColorStop(0.4, 'rgba(255,200,100,0.4)'); grad.addColorStop(1, 'rgba(255,200,100,0)');
                    ctx.fillStyle = grad; ctx.fill();
                } else {
                    let grad = ctx.createRadialGradient(screenX - r*0.3, screenY - r*0.3, r*0.1, screenX, screenY, r * 1.05);
                    grad.addColorStop(0, p.color1); grad.addColorStop(1, p.color2); ctx.fillStyle = grad; ctx.fill();
                    let glow = ctx.createRadialGradient(screenX, screenY, r, screenX, screenY, r * 1.5);
                    let rgbaBase = p.color1 === '#2ec4b6' ? '46, 196, 182' : p.color1 === '#fdb833' ? '253, 184, 51' : p.color1 === '#f72585' ? '247, 37, 133' : p.color1 === '#4cc9f0' ? '76, 201, 240' : p.color1 === '#8338ec' ? '131, 56, 236' : '67, 97, 238';
                    glow.addColorStop(0, `rgba(${rgbaBase}, 0.5)`); glow.addColorStop(1, `rgba(${rgbaBase}, 0)`);
                    ctx.fillStyle = glow; ctx.fill();
                }

                if (p.hasRing) {
                     ctx.beginPath();
                     ctx.ellipse(screenX, screenY, r*2.4, r*0.5, Math.sin(p.angle)*0.5, 0, Math.PI*2);
                     ctx.strokeStyle = `rgba(255,255,255,${Math.min(0.5, 800/dz)})`; ctx.lineWidth = 1.8 * scale; ctx.stroke();
                }

                if (p.name === 'Contact') {
                    let floatOffset = Math.sin(time*2) * 10 * scale;
                    let fx = screenX + (r * 0.3), fy = screenY - r - (50 * scale) + floatOffset;
                    let opacityFlag = Math.min(1, Math.max(0, scrollProgress - 0.7) * 3.33); 
                    ctx.globalAlpha = opacityFlag;
                    ctx.beginPath(); ctx.moveTo(fx, fy); ctx.lineTo(fx, fy - (120*scale)); ctx.strokeStyle='#cccccc'; ctx.lineWidth=2*scale; ctx.stroke();
                    ctx.beginPath(); ctx.moveTo(fx, fy - (120*scale)); ctx.lineTo(fx + (80*scale), fy - (105*scale) + Math.sin(time*5)*5*scale); ctx.lineTo(fx, fy - (80*scale)); ctx.fillStyle='#ef476f'; ctx.fill();
                    ctx.fillStyle = '#ffffff'; ctx.font = `800 ${Math.max(10, 12*scale)}px Inter`; ctx.textAlign='left'; ctx.fillText("SAMUEL", fx + (8*scale), fy - (96*scale));
                    ctx.globalAlpha = 1; 
                }

                let opacity = Math.min(1, 1500/dz); if (dz < 150) opacity *= (dz/150); 
                if (opacity > 0 && p.name !== "") {
                    ctx.fillStyle = `rgba(255,255,255,${opacity})`; ctx.textAlign='center';
                    ctx.font = `800 ${Math.max(12, Math.min(40, 24*scale))}px Inter`;
                    ctx.fillText(p.name, screenX, screenY + r + Math.max(20, 30*scale));
                }
            }
        }
        requestAnimationFrame(animate3D);
    }
    generateScene();
    animate3D();
});
