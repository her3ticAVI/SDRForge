let homeLat = 0.0000;
let homeLon = 0.0000;

let realLat = homeLat;
let realLon = homeLon;

let spoofLat = homeLat;
let spoofLon = homeLon;

let carryOffInterval = null;

const map = L.map("map").setView([spoofLat, spoofLon], 3);

L.tileLayer(
    "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    {
        attribution: "&copy; OpenStreetMap contributors"
    }
).addTo(map);

const realMarker = L.marker([realLat, realLon]).addTo(map);

realMarker.bindPopup("Real GPS Location");

const spoofMarker = L.marker([spoofLat, spoofLon]).addTo(map);

spoofMarker.bindPopup("Spoofed GPS Location");


function setLocation(lat, lon, modeText) {
    homeLat = lat;
    homeLon = lon;

    realLat = lat;
    realLon = lon;

    spoofLat = lat;
    spoofLon = lon;

    realMarker.setLatLng([realLat, realLon]);

    spoofMarker.setLatLng([spoofLat, spoofLon]);

    map.setView([spoofLat, spoofLon], 15);

    updateDisplay(modeText);
}


function updateDisplay(currentMode) {
    document.getElementById("realCoords").innerText =
        `REAL: ${realLat.toFixed(6)}, ${realLon.toFixed(6)}`;

    document.getElementById("spoofCoords").innerText =
        `SPOOFED: ${spoofLat.toFixed(6)}, ${spoofLon.toFixed(6)}`;

    document.getElementById("mode").innerText =
        `MODE: ${currentMode}`;

    spoofMarker.setLatLng([spoofLat, spoofLon]);

    map.panTo([spoofLat, spoofLon]);
}


function getLiveLocation() {
    updateDisplay("REQUESTING LIVE LOCATION");

    if (!navigator.geolocation) {
        getIpLocation();

        return;
    }

    navigator.geolocation.getCurrentPosition(
        function(position) {
            setLocation(
                position.coords.latitude,
                position.coords.longitude,
                "LIVE BROWSER LOCATION"
            );
        },

        function(error) {
            console.log("Browser GPS failed:", error);

            getIpLocation();
        },

        {
            enableHighAccuracy: true,
            timeout: 15000,
            maximumAge: 0
        }
    );
}


function getIpLocation() {
    updateDisplay(
        "BROWSER GPS FAILED - TRYING IP LOCATION"
    );

    fetch("https://ipapi.co/json/")
        .then(response => response.json())

        .then(data => {
            if (data.latitude && data.longitude) {
                setLocation(
                    parseFloat(data.latitude),
                    parseFloat(data.longitude),
                    "IP-BASED LOCATION"
                );
            }

            else {
                updateDisplay(
                    "LOCATION FAILED - USING 0,0 DEFAULT"
                );
            }
        })

        .catch(error => {
            console.log("IP location failed:", error);

            updateDisplay(
                "LOCATION FAILED - USING 0,0 DEFAULT"
            );
        });
}


function scrambleLocation() {
    stopCarryOff();

    spoofLat = (Math.random() * 140) - 70;
    spoofLon = (Math.random() * 360) - 180;

    updateDisplay("SCRAMBLE");
}


function driftLocation() {
    stopCarryOff();

    spoofLat += (Math.random() - 0.5) * 0.02;
    spoofLon += (Math.random() - 0.5) * 0.02;

    updateDisplay("DRIFT");
}


function startCarryOff() {
    stopCarryOff();

    carryOffInterval = setInterval(() => {
        spoofLat += 0.0015;
        spoofLon += 0.0015;

        updateDisplay("CARRY-OFF");

    }, 700);
}


function stopCarryOff() {
    if (carryOffInterval !== null) {
        clearInterval(carryOffInterval);

        carryOffInterval = null;
    }
}


function returnHome() {
    stopCarryOff();

    spoofLat = homeLat;
    spoofLon = homeLon;

    updateDisplay("RETURN HOME");
}


setInterval(() => {
    fetch("/heartbeat")
        .catch(() => {});

}, 1000);


updateDisplay("STARTING");

getLiveLocation();