import * as THREE from "three";
import { OrbitControls } from "OrbitControls";

let scene, camera, renderer, ws, sun, controls, raycaster, mouse, tooltip, selectPlanet = null, hoveredPlanet = null;
const planets = {};
const beams = {};          
let tier = "LOW_END";      
let maxPlanets = 100;

function setTier(tier1) {
    tier = tier1;
    if (tier === "HIGH_END") {
        maxPlanets = 200;
    } else {
        maxPlanets = 100;
    }
    const ids = Object.keys(planets);
    if (ids.length <= maxPlanets) return;
    for (let i = 0; i < (ids.length - maxPlanets); i++) {
        removePlanet(ids[i]);
    }
    console.log(`Tier: ${tier}, maxPlanets = ${maxPlanets}`);

}

function initRenderer(tier) {
    scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x000000, 0.002);
    camera = new THREE.PerspectiveCamera(
        70,
        window.innerWidth / window.innerHeight,
        0.1,
        1000
    );
   
    camera.position.set(0, 40, 70);
    camera.lookAt(0, 0, 0);
    renderer = new THREE.WebGLRenderer({
        antialias: tier !== "LOW_END",
        powerPreference: "high-performance"
    });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = tier !== "LOW_END";
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;


    document.body.appendChild(renderer.domElement);

    controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.enablePan = false;
    controls.minDistance = 20;
    controls.maxDistance = 120;
    controls.target.set(0, 0, 0);
    controls.update();
    const light = new THREE.PointLight(0xffffff, 1.2);
    light.position.set(0, 0, 0);
    scene.add(light);

    scene.add(new THREE.AmbientLight(0x404040));

    sunMesh();

    raycaster = new THREE.Raycaster();
    mouse = new THREE.Vector2();

    const tooltip = document.createElement("div");
    tooltip.id = "planet-tooltip";
    tooltip.style.position = "fixed";
    tooltip.style.pointerEvents = "none";
    tooltip.style.background = "rgba(0,0,0,0.75)";
    tooltip.style.color = "#fff";
    tooltip.style.padding = "6px 8px";
    tooltip.style.borderRadius = "6px";
    tooltip.style.fontSize = "12px";
    tooltip.style.display = "none";
    tooltip.style.zIndex = "1000";
    document.body.appendChild(tooltip);
    }

function registerPlanet(id, mesh) {
    planets[id] = mesh;
    scene.add(mesh);
}

function removePlanet(id) {
    const mesh = planets[id];
    if (!mesh) return;

    scene.remove(mesh);
    mesh.geometry.dispose();
    mesh.material.dispose();
    delete planets[id];

    if (beams[id]) {
        scene.remove(beams[id]);
        beams[id].geometry.dispose();
        beams[id].material.dispose();
        delete beams[id];
    }
}

function sunMesh() {
    const geometry = tier === "HIGH_END" ? new THREE.SphereGeometry(4 * 2, 32, 32) : new THREE.IcosahedronGeometry(4 * 2, 1);
    const material = new THREE.MeshStandardMaterial({
        color: 0xffdd55,
        emissive: 0xffee88,
        emissiveIntensity: 2.0
    });
    sun = new THREE.Mesh(geometry, material);
    sun.position.set(0, 0, 0);
    scene.add(sun);
    const sunLight = new THREE.PointLight(0xfff2cc, 2.2, 220);
    sunLight.position.set(0, 0, 0);
    sunLight.castShadow = tier !== "LOW_END";
    scene.add(sunLight);
}

function createPlanetMesh(tier, isThreat) {
    const geometry =
        tier === "HIGH_END"
            ? new THREE.SphereGeometry(2.5 * 2, 32, 32)
            : new THREE.IcosahedronGeometry(2 * 2, 0);

    const material = new THREE.MeshStandardMaterial({
        color: isThreat ? 0xff3333 : 0x33ff99,
        emissive: isThreat ? 0xff0000 : 0x000000,
        emissiveIntensity: isThreat ? 0.6 : 0.0,
        flatShading: tier === "LOW_END"
    });

    const mesh = new THREE.Mesh(geometry, material);

    mesh.castShadow = tier !== "LOW_END";
    mesh.receiveShadow = tier !== "LOW_END";

    mesh.targetPosition = new THREE.Vector3();

    mesh.orbitAngle = Math.random() * Math.PI * 2;
    mesh.orbitSpeed = (0.01 + Math.random() * 0.02);

    mesh.isThreat = isThreat;
    mesh.pulsePhase = Math.random() * Math.PI * 2;

    return mesh;
}


function computeOrbitPosition(conn, index) {
    const planet = planets[conn.id];
    if (!planet) return new THREE.Vector3();

    const radius = 15 + (index % 10) * 3;
    const yOffset = (index % 5) * 1.2;

    return new THREE.Vector3(
        Math.cos(planet.orbitAngle) * planet.orbitRadius,
        yOffset,
        Math.sin(planet.orbitAngle) * planet.orbitRadius
    );
}

function createBeam(id, position, index) {
    if (tier === "LOW_END" && Object.keys(planets).length > 50) return;

    const offset = ((index % 5) - 2) * 0.5;
    const points = [
        new THREE.Vector3(0, offset, 0),
        position
    ];

    const geometry = new THREE.BufferGeometry().setFromPoints(points);
    const material = new THREE.LineBasicMaterial({
        color: 0x4444ff,
        transparent: true,
        opacity: 0.3
    });

    const line = new THREE.Line(geometry, material);
    beams[id] = line;
    scene.add(line);
}

function updateFromPacket(packet) {
    console.log("Backend tier:", packet.meta?.tier, "| Current tier:", tier);
    if (packet.meta?.tier && packet.meta.tier !== tier) {
        setTier(packet.meta.tier);
    }

    const seen = new Set();

    packet.connections.forEach((conn, index) => {
        const id = conn.id;
        seen.add(id);
        const radius = 35 + (index) * 5;

        if (!planets[id]) {
            if (Object.keys(planets).length >= maxPlanets) return;

            const mesh = createPlanetMesh(tier, conn.is_threat);
            mesh.userData = {
                app: conn.app,
                ip: conn.ip,
                port: conn.port,
                pid: conn.pid,
                "type": conn.type,
                "domain": conn.domain,
                isThreat: conn.is_threat
            };

            mesh.orbitRadius = radius;
            mesh.orbitAngle = Math.random() * Math.PI * 2; 
            mesh.orbitSpeed = 0.085 / radius;
            mesh.connectionData = conn;
            registerPlanet(id, mesh);
        }

        const targetPos = computeOrbitPosition(conn, index);
        planets[id].targetPosition.copy(targetPos);

        if (!beams[id]) {
            createBeam(id, targetPos, index);
        }
    });

    Object.keys(planets).forEach(id => {
        if (!seen.has(id)) {
            removePlanet(id);
        }
    });
}

function animate() {
    requestAnimationFrame(animate);

    const tooltip = document.getElementById("planet-tooltip");

    const activePlanet = selectPlanet || hoveredPlanet;
    if (activePlanet) {
        const d = activePlanet.userData;
        const vector = activePlanet.position.clone();
        vector.project(camera);
        const x = (vector.x * 0.5 + 0.5) * window.innerWidth;
        const y = (-vector.y * 0.5 + 0.5) * window.innerHeight;

        tooltip.style.left = `${x+12}px`;
        tooltip.style.top = `${y+12}px`;
        tooltip.style.display = "block";

        tooltip.innerHTML = `
            <strong>${d.type === "browser" ? "Browser Connection" : "Process"}</strong><br>
            ${d.type === "browser" ? `Browser: ${d.app}<br>Site: ${d.domain || d.ip}<br>` : `App: ${d.app}<br>`}
            IP: ${d.ip}:${d.port}<br>
            ${d.isThreat ? "🔴 Malicious" : "🟢 Normal"}
        `;
    } else {
        tooltip.style.display = "none";
    }

    raycaster.setFromCamera(mouse, camera);

    

    //if (intersects.length > 0) {
    //    const planet = intersects[0].object;
    //    const d = planet.userData;
//
    //    if (d) {
    //        tooltip.style.display = "block";
    //        tooltip.innerHTML = `
    //            <strong>${d.app}</strong><br/>
    //            IP: ${d.ip}:${d.port}<br/>
    //            PID: ${d.pid}<br/>
    //            ${d.isThreat ? "Malicious" : "Normal"}
    //        `;
    //    }
    //} else {
    //    tooltip.style.display = "none";
    //}


    if (sun) {
        const scale = 1 + Math.sin(Date.now() * 0.002) * 0.03;
        sun.scale.set(scale, scale, scale);
    }

    Object.values(planets).forEach(planet => {
    planet.orbitAngle += planet.orbitSpeed;

    planet.targetPosition.set(
        Math.cos(planet.orbitAngle) * planet.orbitRadius,
        planet.position.y,
        Math.sin(planet.orbitAngle) * planet.orbitRadius
    );

    planet.position.lerp(planet.targetPosition, 0.08);

    if (planet.isThreat) {
        planet.pulsePhase += 0.05;
        planet.material.emissiveIntensity =
            0.6 + Math.sin(planet.pulsePhase) * 0.4;
    }
});

    Object.keys(beams).forEach(id => {
        const beam = beams[id];
        const planet = planets[id];
        if (!planet) return;

        const pos = planet.position;
        beam.geometry.setFromPoints([
            new THREE.Vector3(0, 0, 0),
            pos
        ]);
    });

    controls.update()

    renderer.render(scene, camera);
}

function initWebSocket() {
    ws = new WebSocket("ws://127.0.0.1:8000/ws");

    ws.onopen = () => {
        console.log("WebSocket connected");
    };

    ws.onmessage = (event) => {
        console.log("Packet received");
        try {
            const packet = JSON.parse(event.data);
            updateFromPacket(packet);
        } catch (e) {
            console.error("Invalid packet", e);
        }
    };

    ws.onclose = () => {
        console.warn("WS closed, retrying");
        setTimeout(initWebSocket, 2000);
    };
}

setTier("LOW_END");
initRenderer(tier);
initWebSocket();
animate();

window.addEventListener("mousemove", (event) => {
    mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
    mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;

    raycaster.setFromCamera(mouse, camera);
    const intersects = raycaster.intersectObjects(Object.values(planets));
    if (intersects.length > 0) {
        hoveredPlanet = intersects[0].object;
        document.body.style.cursor = 'pointer';
    } else {
        hoveredPlanet = null;
        document.body.style.cursor = 'default';
    }
});

window.addEventListener("click", () => {
    if (hoveredPlanet) {
        selectPlanet = hoveredPlanet;
    } else {
        selectPlanet = null;
    }
})

window.addEventListener("resize", () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});
