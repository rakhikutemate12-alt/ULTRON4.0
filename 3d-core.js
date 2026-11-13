
(() => {
    "use strict";

    const canvas = document.getElementById("ultron3d");
    if (!canvas) return;

    const fallback = document.querySelector(".core-fallback");
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    let THREE;
    let renderer;
    let scene;
    let camera;
    let core;
    let rings = [];
    let particles;
    let animationFrame;
    let state = "idle";
    let lastTime = 0;
    let width = 0;
    let height = 0;

    const mobile = window.matchMedia("(max-width: 700px)").matches;
    const particleCount = mobile ? 220 : 420;

    function setState(nextState) {
        state = ["idle", "thinking", "speaking", "listening"].includes(nextState)
            ? nextState
            : "idle";

        canvas.dataset.state = state;
    }

    async function initialize() {
        try {
            THREE = await import(
                "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js"
            );

            scene = new THREE.Scene();
            camera = new THREE.PerspectiveCamera(42, 1, 0.1, 100);
            camera.position.set(0, 0, 7.5);

            renderer = new THREE.WebGLRenderer({
                canvas,
                alpha: true,
                antialias: !mobile,
                powerPreference: "low-power"
            });

            renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
            renderer.setClearColor(0x000000, 0);

            const ambient = new THREE.AmbientLight(0x6688ff, 1.7);
            scene.add(ambient);

            const blueLight = new THREE.PointLight(0x00cfff, 35, 12);
            blueLight.position.set(2, 2, 4);
            scene.add(blueLight);

            const violetLight = new THREE.PointLight(0x7744ff, 28, 12);
            violetLight.position.set(-2, -2, 2);
            scene.add(violetLight);

            const coreGeometry = new THREE.IcosahedronGeometry(1.05, 2);

            const coreMaterial = new THREE.MeshPhysicalMaterial({
                color: 0x087fca,
                emissive: 0x003b75,
                emissiveIntensity: 1.8,
                metalness: 0.72,
                roughness: 0.22,
                clearcoat: 1,
                clearcoatRoughness: 0.16,
                flatShading: false
            });

            core = new THREE.Mesh(coreGeometry, coreMaterial);
            scene.add(core);

            const wire = new THREE.Mesh(
                new THREE.IcosahedronGeometry(1.11, 1),
                new THREE.MeshBasicMaterial({
                    color: 0x35dfff,
                    wireframe: true,
                    transparent: true,
                    opacity: 0.28
                })
            );

            core.add(wire);

            const ringSpecs = [
                { radius: 1.55, tube: 0.018, color: 0x00dfff, x: 0.7, y: 0.3 },
                { radius: 1.72, tube: 0.012, color: 0x8260ff, x: 1.3, y: 0.8 },
                { radius: 1.9, tube: 0.01, color: 0x168cff, x: 0.2, y: 1.1 }
            ];

            ringSpecs.forEach(spec => {
                const geometry = new THREE.TorusGeometry(
                    spec.radius,
                    spec.tube,
                    8,
                    120
                );

                const material = new THREE.MeshBasicMaterial({
                    color: spec.color,
                    transparent: true,
                    opacity: 0.8
                });

                const ring = new THREE.Mesh(geometry, material);
                ring.rotation.set(spec.x, spec.y, 0);
                scene.add(ring);
                rings.push(ring);
            });

            const positions = new Float32Array(particleCount * 3);

            for (let i = 0; i < particleCount; i++) {
                const radius = 2.1 + Math.random() * 2.0;
                const angle = Math.random() * Math.PI * 2;
                const vertical = (Math.random() - 0.5) * 4.2;

                positions[i * 3] = Math.cos(angle) * radius;
                positions[i * 3 + 1] = vertical;
                positions[i * 3 + 2] = Math.sin(angle) * radius;
            }

            const particleGeometry = new THREE.BufferGeometry();
            particleGeometry.setAttribute(
                "position",
                new THREE.BufferAttribute(positions, 3)
            );

            const particleMaterial = new THREE.PointsMaterial({
                color: 0x45cfff,
                size: 0.025,
                transparent: true,
                opacity: 0.8,
                sizeAttenuation: true
            });

            particles = new THREE.Points(
                particleGeometry,
                particleMaterial
            );

            scene.add(particles);

            if (fallback) fallback.style.display = "none";

            resize();
            window.addEventListener("resize", resize);
            document.addEventListener("visibilitychange", visibilityChanged);

            if (!reducedMotion) {
                animate(0);
            } else {
                renderer.render(scene, camera);
            }

            console.log("ULTRON 3D core initialized.");

        } catch (error) {
            console.error("ULTRON 3D initialization failed:", error);
            if (fallback) fallback.style.display = "grid";
        }
    }

    function resize() {
        if (!renderer || !canvas.parentElement) return;

        const rect = canvas.parentElement.getBoundingClientRect();

        width = Math.max(1, rect.width);
        height = Math.max(1, rect.height);

        camera.aspect = width / height;
        camera.updateProjectionMatrix();

        renderer.setSize(width, height, false);
    }

    function visibilityChanged() {
        if (document.hidden) {
            cancelAnimationFrame(animationFrame);
            animationFrame = null;
        } else if (!reducedMotion && !animationFrame) {
            lastTime = 0;
            animate(0);
        }
    }

    function animate(time) {
        if (document.hidden || !renderer) {
            animationFrame = null;
            return;
        }

        animationFrame = requestAnimationFrame(animate);

        const delta = lastTime ? Math.min((time - lastTime) / 1000, 0.05) : 0;
        lastTime = time;

        const speed = state === "thinking" ? 2.8 :
                      state === "listening" ? 1.7 :
                      state === "speaking" ? 2.0 : 0.55;

        const pulse = state === "thinking" ? 1.13 :
                      state === "speaking" ? 1.09 :
                      state === "listening" ? 1.05 :
                      1 + Math.sin(time * 0.0012) * 0.035;

        core.rotation.x += delta * 0.18 * speed;
        core.rotation.y += delta * 0.3 * speed;
        core.scale.setScalar(pulse);

        rings.forEach((ring, index) => {
            const direction = index === 1 ? -1 : 1;
            ring.rotation.z += delta * speed * direction * (0.12 + index * 0.06);
        });

        particles.rotation.y += delta * 0.035 * speed;

        const intensity = state === "thinking" ? 2.8 : 1.8;
        core.material.emissiveIntensity = intensity + Math.sin(time * 0.003) * 0.25;

        renderer.render(scene, camera);
    }

    window.ULTRON_3D = {
        setState,
        getState: () => state
    };

    initialize();
})();
