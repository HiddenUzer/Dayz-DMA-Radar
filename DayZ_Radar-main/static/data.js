// Constants
const mapSelector = document.getElementById("mapSelector");
const pcanvas = document.getElementById('player');
const map_image = document.getElementById('map_image');
const drawCanvas = document.getElementById('draw');
const settings = {
    pi: Math.PI,
    dot: 95,
    mapSize: [15360, 15360],
};

// Canvas Context Initialization
let pctx = pcanvas.getContext('2d');
let drawCtx = drawCanvas.getContext('2d');
// Variables
let currentPercentage = 100;
let socket;
let isDrawing = false;
let scaleFactor = 0.1;

function drawCircle(pctx, x, y, color) {
    pctx.fillStyle = color;
    pctx.beginPath();
    pctx.arc(x, y, 300 / settings.dot, 0, settings.pi * 2);
    pctx.fill();
    pctx.closePath();
};

function drawText(pctx, text, x, y, color) {
    pctx.font = '10px Arial'; // Adjust font size and style as needed
    pctx.fillStyle = color; // Text color
    pctx.fillText(text, x, y);
};

function drawCircleWithLine(pctx, x, y, rotationInRadians, color) {
    // Draw circle
    pctx.fillStyle = color;
    pctx.beginPath();
    pctx.arc(x, y, 300 / settings.dot, 0, settings.pi * 2); // Adjust radius as needed
    pctx.fill();
    
    // Draw line indicating direction
    pctx.strokeStyle = color;
    pctx.lineWidth = 2; // Adjust line width as needed
    pctx.beginPath();
    pctx.moveTo(x, y);

    // Extend the line in the direction of rotation (already in radians)
    let lineLength = 10; // Adjust line length as needed
    let endX = x + lineLength * Math.cos(rotationInRadians);
    let endY = y + lineLength * Math.sin(rotationInRadians);

    pctx.lineTo(endX, endY);
    pctx.stroke();
};

function draw_players(players) {
    for (let i = 0; i < players.length; i++) {
        // Adjust for viewport position and scale
        let x = players[i].x * scaleFactor;
        let y = (15360 - players[i].y) * scaleFactor;

        // Use a more specific variable name
        let playerName = players[i].name;
        let color;

        // Simplify color assignment logic with a switch statement
        switch (playerName) {
            case 'zombie':
                color = 'rgb(170, 255, 0)';
                drawCircle(pctx, x, y, color);
                break;
            case 'player':
                color = 'rgb(255, 0, 0)';
                drawCircle(pctx, x, y, color);
                drawText(pctx, playerName, x - 10, y - 10, color);
                break;
            case 'RonB':
                drawCircleWithLine(pctx, x, y, players[i].rot, 'rgb(0, 255, 255)');
                break;
        }
    }
};

function adjustCanvasAndImageSize(percentage) {
  currentPercentage = percentage;
  const canvasWidth = settings.mapSize[0] * (percentage / 100);
  const canvasHeight = settings.mapSize[1] * (percentage / 100);
  scaleFactor = canvasWidth / settings.mapSize[0];

  const canvasElements = document.querySelectorAll('canvas');
  canvasElements.forEach(canvas => {
      canvas.width = canvasWidth;
      canvas.height = canvasHeight;
  });
  map_image.width = canvasWidth;
  map_image.height = canvasHeight;
};

document.getElementById('dotSlider').addEventListener('input', function() {
    settings.dot = parseInt(this.value);
    console.log('dotSlider', settings.dot);
});

mapSelector.addEventListener("change", function() {
    const selectedMap = this.value;
    map_image.onload = function() {
        // Calculate scaled dimensions based on the scaleFactor
        const scaledWidth = map_image.naturalWidth * scaleFactor;
        const scaledHeight = map_image.naturalHeight * scaleFactor;
        // Set the image dimensions to match the scaled dimensions
        map_image.width = scaledWidth;
        map_image.height = scaledHeight;
        pcanvas.width = map_image.width;
        pcanvas.height = map_image.height;
        drawCanvas.width = map_image.width;
        drawCanvas.height = map_image.height;
    };
    map_image.src = `static/maps/${selectedMap}.png`;
});

function scaleCoordinates(x, y, percentage) {
    const scaledX = x * (percentage / 100);
    const scaledY = y * (percentage / 100);
    return [scaledX, scaledY];
};

pcanvas.addEventListener('pointerdown', (e) => {
    isDrawing = true;
    [lastXDraw, lastYDraw] = [e.offsetX, e.offsetY];
});

document.getElementById('sizeSlider').addEventListener('input', function() {
    const percentage = parseInt(this.value);
    adjustCanvasAndImageSize(percentage);
});

pcanvas.addEventListener('pointermove', drawOnCanvas);
pcanvas.addEventListener('pointerup', endDrawing);
pcanvas.addEventListener('pointerout', endDrawing);
document.getElementById('clearCanvasBtn').addEventListener('click', clearCanvasAndNotify);
function getNormalizedCoordinates(x, y, percentage) {
    const normalizedX = x / (percentage / 100);
    const normalizedY = y / (percentage / 100);
    return [normalizedX, normalizedY];
}

function drawOnCanvas(e) {
    if (!isDrawing) return;

    drawCtx.strokeStyle = 'rgb(255, 0, 255)';
    drawCtx.lineWidth = 2;
    drawCtx.beginPath();
    drawCtx.moveTo(lastXDraw, lastYDraw);
    drawCtx.lineTo(e.offsetX, e.offsetY);
    drawCtx.stroke();

    const [normalizedX0, normalizedY0] = getNormalizedCoordinates(lastXDraw, lastYDraw, currentPercentage);
    const [normalizedX1, normalizedY1] = getNormalizedCoordinates(e.offsetX, e.offsetY, currentPercentage);
    const data = {
        x0: normalizedX0,
        y0: normalizedY0,
        x1: normalizedX1,
        y1: normalizedY1,
    };

    socket.emit('drawing', data);
    [lastXDraw, lastYDraw] = [e.offsetX, e.offsetY];
}

function endDrawing() {
    isDrawing = false;
}

function clearCanvasAndNotify() {
    clearCanvas();
    socket.emit('clearCanvas');
}

function clearCanvas() {
    drawCtx.clearRect(0, 0, drawCanvas.width, drawCanvas.height);
}

if (!socket) {
    socket = io({
        reconnection: true,
        reconnectionAttempts: Infinity,
        reconnectionDelay: 1000,
        reconnectionDelayMax: 5000,
        randomizationFactor: 0.5,
        timeout: 20000,
        transport: ['websocket']
    });
};

socket.on('connect', () => {
    console.log('socket connected:', socket.id);
});

socket.on('disconnect', () => {
    console.log('socket disconnected');
});

socket.on('force_disconnect', function(){
    socket.disconnect();
    console.log('socket disconnected by server');
})

socket.on('updateData', function(data) {
    if (!data){
        console.error('Received undefined or null player data');
        return;
    }
    // Only handle player data here
    pctx.clearRect(0, 0, pcanvas.width, pcanvas.height);
    draw_players(data);
});

socket.on('clearCanvas', function() {
    clearCanvas();
});

socket.on('drawing', function(data) {
    const [scaledX0, scaledY0] = scaleCoordinates(data.x0, data.y0, currentPercentage);
    const [scaledX1, scaledY1] = scaleCoordinates(data.x1, data.y1, currentPercentage);

    drawCtx.strokeStyle = 'rgb(255, 0, 255)';
    drawCtx.lineWidth = 2;
    drawCtx.beginPath();
    drawCtx.moveTo(scaledX0, scaledY0);
    drawCtx.lineTo(scaledX1, scaledY1);
    drawCtx.stroke();
});

