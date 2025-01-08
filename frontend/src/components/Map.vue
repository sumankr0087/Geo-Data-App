<!-- <template>
  <div class="h-screen flex">
    <div class="w-1/4 bg-white p-4 overflow-y-auto">
      <h2 class="text-lg font-semibold mb-4">Layers</h2>
      <div v-for="file in uploadedFiles" :key="file.id" class="mb-2">
        <label class="flex items-center">
          <input type="checkbox" :value="file.id" v-model="visibleLayers" class="mr-2">
          {{ file.file_type }} - {{ getFileName(file.file) }}
        </label>
      </div>
      <h2 class="text-lg font-semibold mt-6 mb-4">Upload File</h2>
      <form @submit.prevent="uploadFile" class="space-y-4">
        <div>
          <label for="file" class="block text-sm font-medium text-gray-700">Select file</label>
          <input type="file" id="file" ref="fileInput" class="mt-1 block w-full" @change="handleFileChange">
        </div>
        <div>
          <label for="fileType" class="block text-sm font-medium text-gray-700">File type</label>
          <select id="fileType" v-model="fileType" class="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md">
            <option value="GeoJSON">GeoJSON</option>
            <option value="KML">KML</option>
            <option value="TIFF">TIFF</option>
          </select>
        </div>
        <button type="submit" class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
          Upload
        </button>
      </form>
    </div>
    <div class="w-3/4 relative">
      <div id="map" class="h-full"></div>
      <div class="absolute bottom-4 left-4 z-[1000] space-y-2">
        <button @click="toggleDrawing" class="bg-white p-2 rounded-md shadow-md">
          {{ isDrawing ? 'Stop Drawing' : 'Start Drawing' }}
        </button>
        <button @click="toggleMeasuring" class="bg-white p-2 rounded-md shadow-md">
          {{ isMeasuring ? 'Stop Measuring' : 'Start Measuring' }}
        </button>
        <button @click="addMarker" class="bg-white p-2 rounded-md shadow-md">
          Add Marker
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet-draw';
import 'leaflet-draw/dist/leaflet.draw.css';
import axios from 'axios';
import "leaflet-geotiff";
// import "leaflet-geotiff/dist/leaflet-geotiff.css";

const map = ref(null);
const uploadedFiles = ref([]);
const visibleLayers = ref([]);
const fileInput = ref(null);
const fileType = ref('GeoJSON');
const isDrawing = ref(false);
const isMeasuring = ref(false);
const drawControl = ref(null);
const measureControl = ref(null);
const drawnItems = ref(null);
const markers = ref([]);

onMounted(async () => {
  initMap();
  await fetchUploadedFiles();
});

watch(visibleLayers, () => {
  updateMapLayers();
});

function initMap() {
  map.value = L.map('map').setView([0, 0], 2);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
  }).addTo(map.value);

  drawnItems.value = new L.FeatureGroup();
  map.value.addLayer(drawnItems.value);

  drawControl.value = new L.Control.Draw({
    edit: {
      featureGroup: drawnItems.value
    },
    draw: {
      polygon: true,
      polyline: true,
      rectangle: true,
      circle: true,
      marker: false
    }
  });
  map.value.addControl(drawControl.value);

  map.value.on(L.Draw.Event.CREATED, (event) => {
    const layer = event.layer;
    drawnItems.value.addLayer(layer);
  });

  measureControl.value = new L.Control.Measure({
    primaryLengthUnit: 'kilometers',
    secondaryLengthUnit: 'miles',
    primaryAreaUnit: 'sqmeters',
    secondaryAreaUnit: 'acres'
  });
  map.value.addControl(measureControl.value);
}

async function fetchUploadedFiles() {
  try {
    const response = await axios.get('http://127.0.0.1:8000/api/upload/files/', {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('token')}`
      }
    });
    uploadedFiles.value = response.data;
  } catch (error) {
    console.error('Error fetching uploaded files:', error);
  }
}

function updateMapLayers() {
  // Clear existing layers
  map.value.eachLayer((layer) => {
    if (layer instanceof L.GeoJSON || layer.options?.isTIFF) {
      map.value.removeLayer(layer);
    }
  });

  visibleLayers.value.forEach((layerId) => {
    const file = uploadedFiles.value.find((f) => f.id === layerId);

    if (file) {
      if (file.file_type === "GeoJSON" || file.file_type === "KML") {
        fetch(file.file)
          .then((response) => response.json())
          .then((data) => {
            L.geoJSON(data, {
              onEachFeature: (feature, layer) => {
                layer.bindPopup(`<div>${JSON.stringify(feature.properties)}</div>`);
              },
            }).addTo(map.value);
          })
          .catch((error) => console.error("Error loading GeoJSON/KML:", error));
      } else if (file.file_type === "TIFF") {
        // Load TIFF file
        fetch(file.file)
          .then((response) => response.arrayBuffer())
          .then((arrayBuffer) => {
            const tiffLayer = L.leafletGeotiff(arrayBuffer, {
              renderer: L.LeafletGeotiffRenderer(),
              isTIFF: true, // Custom option to identify TIFF layers
            }).addTo(map.value);
          })
          .catch((error) => console.error("Error loading TIFF:", error));
      }
    }
  });
}


function getFileName(url) {
  return url.split('/').pop();
}

async function uploadFile() {
  if (!fileInput.value.files.length) return;

  const formData = new FormData();
  formData.append('file', fileInput.value.files[0]);
  formData.append('file_type', fileType.value);

  try {
    await axios.post('http://127.0.0.1:8000/api/upload/upload/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      }
    });
    await fetchUploadedFiles();
    fileInput.value.value = '';
  } catch (error) {
    console.error('Error uploading file:', error);
  }
}

function handleFileChange(event) {
  const file = event.target.files[0];
  if (file) {
    const extension = file.name.split('.').pop().toLowerCase();
    if (extension === 'geojson') {
      fileType.value = 'GeoJSON';
    } else if (extension === 'kml') {
      fileType.value = 'KML';
    } else if (extension === 'tif' || extension === 'tiff') {
      fileType.value = 'TIFF';
    }
  }
}

function toggleDrawing() {
  isDrawing.value = !isDrawing.value;
  if (isDrawing.value) {
    map.value.addControl(drawControl.value);
  } else {
    map.value.removeControl(drawControl.value);
  }
}

function toggleMeasuring() {
  isMeasuring.value = !isMeasuring.value;
  if (isMeasuring.value) {
    map.value.addControl(measureControl.value);
  } else {
    map.value.removeControl(measureControl.value);
  }
}

function addMarker() {
  const marker = L.marker([0, 0], { draggable: true }).addTo(map.value);
  markers.value.push(marker);

  marker.on('dragend', () => {
    const position = marker.getLatLng();
    marker.bindPopup(`Latitude: ${position.lat.toFixed(4)}, Longitude: ${position.lng.toFixed(4)}`).openPopup();
  });
}
</script>

<style>
@import 'leaflet/dist/leaflet.css';
@import 'leaflet-draw/dist/leaflet.draw.css';
</style>
 -->

 <template>
  <div class="h-screen flex">
    <div class="w-1/4 bg-white p-4 overflow-y-auto">
      <h2 class="text-lg font-semibold mb-4">Layers</h2>
      <div v-for="file in uploadedFiles" :key="file.id" class="mb-2">
        <label class="flex items-center">
          <input type="checkbox" :value="file.id" v-model="visibleLayers" class="mr-2">
          {{ file.file_type }} - {{ getFileName(file.file) }}
        </label>
      </div>
      <h2 class="text-lg font-semibold mt-6 mb-4">Upload File</h2>
      <form @submit.prevent="uploadFile" class="space-y-4">
        <div>
          <label for="file" class="block text-sm font-medium text-gray-700">Select file</label>
          <input type="file" id="file" ref="fileInput" class="mt-1 block w-full" @change="handleFileChange">
        </div>
        <div>
          <label for="fileType" class="block text-sm font-medium text-gray-700">File type</label>
          <select id="fileType" v-model="fileType" class="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md">
            <option value="GeoJSON">GeoJSON</option>
            <option value="KML">KML</option>
            <option value="TIFF">TIFF</option>
          </select>
        </div>
        <button type="submit" class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
          Upload
        </button>
      </form>
    </div>
    <div class="w-3/4 relative">
      <div id="map" class="h-full"></div>
      <div class="absolute bottom-4 left-4 z-[1000] space-y-2">
        <button @click="toggleDrawing" 
                class="bg-white p-2 rounded-md shadow-md hover:bg-gray-50">
          {{ isDrawing ? 'Stop Drawing' : 'Start Drawing' }}
        </button>
        <button @click="toggleMeasuring" 
                class="bg-white p-2 rounded-md shadow-md hover:bg-gray-50">
          {{ isMeasuring ? 'Stop Measuring' : 'Start Measuring' }}
        </button>
        <button @click="addMarker" 
                class="bg-white p-2 rounded-md shadow-md hover:bg-gray-50">
          Add Marker
        </button>
        <button @click="saveShapes" 
                class="bg-white p-2 rounded-md shadow-md hover:bg-gray-50">
          Save Shapes
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet-draw';
import 'leaflet-draw/dist/leaflet.draw.css';
import axios from 'axios';
import "@geoman-io/leaflet-geoman-free";
import "@geoman-io/leaflet-geoman-free/dist/leaflet-geoman.css";

const map = ref(null);
const uploadedFiles = ref([]);
const visibleLayers = ref([]);
const fileInput = ref(null);
const fileType = ref('GeoJSON');
const isDrawing = ref(false);
const isMeasuring = ref(false);
const drawControl = ref(null);
const measureControl = ref(null);
const drawnItems = ref(null);
const markers = ref([]);
const layerGroups = ref({});

onMounted(async () => {
  initMap();
  await fetchUploadedFiles();
});

watch(visibleLayers, () => {
  updateMapLayers();
});

function initMap() {
  // Initialize map
  map.value = L.map('map').setView([0, 0], 2);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
  }).addTo(map.value);

  // Initialize drawing feature group
  drawnItems.value = new L.FeatureGroup();
  map.value.addLayer(drawnItems.value);

  // Initialize Geoman controls
  map.value.pm.addControls({
    position: 'topleft',
    drawCircle: true,
    drawMarker: true,
    drawPolygon: true,
    drawPolyline: true,
    drawRectangle: true,
    editMode: true,
    dragMode: true,
    removalMode: true,
  });

  // Set up hover events for shapes
  map.value.on('pm:create', (e) => {
    const layer = e.layer;
    setupLayerHoverEvents(layer);
    drawnItems.value.addLayer(layer);
  });

  // Initialize measurement control
  initMeasurementControl();

  // Load saved shapes
  loadSavedShapes();
}

function setupLayerHoverEvents(layer) {
  layer.on('mouseover', (e) => {
    const popup = L.popup({
      className: 'hover-card',
      closeButton: false,
      offset: [0, -10]
    });

    let content = '';
    if (layer instanceof L.Marker) {
      const latlng = layer.getLatLng();
      content = `Location: ${latlng.lat.toFixed(4)}, ${latlng.lng.toFixed(4)}`;
    } else if (layer instanceof L.Polygon) {
      const area = L.GeometryUtil.geodesicArea(layer.getLatLngs()[0]);
      content = `Area: ${(area / 1000000).toFixed(2)} km²`;
    } else if (layer instanceof L.Polyline) {
      const distance = calculateDistance(layer);
      content = `Distance: ${distance.toFixed(2)} km`;
    }

    popup.setContent(content)
         .setLatLng(e.latlng)
         .openOn(map.value);
  });

  layer.on('mouseout', () => {
    map.value.closePopup();
  });
}

function calculateDistance(layer) {
  let distance = 0;
  const latlngs = layer.getLatLngs();
  
  for (let i = 0; i < latlngs.length - 1; i++) {
    distance += latlngs[i].distanceTo(latlngs[i + 1]);
  }
  
  return distance / 1000; // Convert to kilometers
}

function initMeasurementControl() {
  measureControl.value = L.control.measure({
    primaryLengthUnit: 'kilometers',
    secondaryLengthUnit: 'miles',
    primaryAreaUnit: 'sqmeters',
    secondaryAreaUnit: 'acres',
    activeColor: '#3388ff',
    completedColor: '#33ff88'
  });
}

async function fetchUploadedFiles() {
  try {
    const response = await axios.get('http://127.0.0.1:8000/api/upload/files/', {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('token')}`
      }
    });
    uploadedFiles.value = response.data;
  } catch (error) {
    console.error('Error fetching files:', error);
  }
}

function updateMapLayers() {
  // Clear existing layers except base layer
  Object.values(layerGroups.value).forEach(group => {
    map.value.removeLayer(group);
  });

  // Add selected layers
  visibleLayers.value.forEach(async (layerId) => {
    const file = uploadedFiles.value.find(f => f.id === layerId);
    if (!file) return;

    if (!layerGroups.value[layerId]) {
      const group = new L.FeatureGroup();
      layerGroups.value[layerId] = group;

      try {
        const response = await fetch(file.file);
        const data = await response.json();
        
        L.geoJSON(data, {
          onEachFeature: (feature, layer) => {
            setupLayerHoverEvents(layer);
            layer.bindPopup(createPopupContent(feature));
          }
        }).addTo(group);
      } catch (error) {
        console.error('Error loading layer:', error);
      }
    }

    map.value.addLayer(layerGroups.value[layerId]);
  });
}

function createPopupContent(feature) {
  if (!feature.properties) return 'No properties available';
  
  return Object.entries(feature.properties)
    .map(([key, value]) => `<strong>${key}:</strong> ${value}`)
    .join('<br>');
}

function getFileName(url) {
  return url.split('/').pop();
}

async function uploadFile() {
  if (!fileInput.value.files.length) return;

  const formData = new FormData();
  formData.append('file', fileInput.value.files[0]);
  formData.append('file_type', fileType.value);

  try {
    const response = await axios.post('http://127.0.0.1:8000/api/upload/upload/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
        Authorization: `Bearer ${localStorage.getItem('token')}`
      }
    });
    
    await fetchUploadedFiles();
    fileInput.value.value = '';
    
    // Automatically show the new layer
    visibleLayers.value.push(response.data.id);
  } catch (error) {
    console.error('Error uploading file:', error);
  }
}

function handleFileChange(event) {
  const file = event.target.files[0];
  if (!file) return;

  const extension = file.name.split('.').pop().toLowerCase();
  if (extension === 'geojson') {
    fileType.value = 'GeoJSON';
  } else if (extension === 'kml') {
    fileType.value = 'KML';
  } else if (extension === 'tif' || extension === 'tiff') {
    fileType.value = 'TIFF';
  }
}

function toggleDrawing() {
  isDrawing.value = !isDrawing.value;
  if (isDrawing.value) {
    map.value.pm.enableDraw('Polygon');
  } else {
    map.value.pm.disableDraw();
  }
}

function toggleMeasuring() {
  isMeasuring.value = !isMeasuring.value;
  if (isMeasuring.value) {
    measureControl.value.addTo(map.value);
  } else {
    measureControl.value.remove();
  }
}

function addMarker() {
  const center = map.value.getCenter();
  const marker = L.marker(center, {
    draggable: true
  }).addTo(map.value);

  marker.on('dragend', () => {
    const pos = marker.getLatLng();
    marker.bindPopup(`Lat: ${pos.lat.toFixed(4)}<br>Lng: ${pos.lng.toFixed(4)}`).openPopup();
  });

  markers.value.push(marker);
  setupLayerHoverEvents(marker);
}

async function saveShapes() {
  const shapes = [];
  drawnItems.value.eachLayer((layer) => {
    if (layer instanceof L.Marker) {
      shapes.push({
        type: 'marker',
        coordinates: layer.getLatLng()
      });
    } else if (layer instanceof L.Polygon) {
      shapes.push({
        type: 'polygon',
        coordinates: layer.getLatLngs()
      });
    } else if (layer instanceof L.Polyline) {
      shapes.push({
        type: 'polyline',
        coordinates: layer.getLatLngs()
      });
    }
  });

  try {
    await axios.post('http://127.0.0.1:8000/api/shapes/save', shapes, {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('token')}`
      }
    });
  } catch (error) {
    console.error('Error saving shapes:', error);
  }
}

async function loadSavedShapes() {
  try {
    const response = await axios.get('http://127.0.0.1:8000/api/shapes', {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('token')}`
      }
    });

    response.data.forEach(shape => {
      let layer;
      if (shape.type === 'marker') {
        layer = L.marker(shape.coordinates, { draggable: true });
      } else if (shape.type === 'polygon') {
        layer = L.polygon(shape.coordinates);
      } else if (shape.type === 'polyline') {
        layer = L.polyline(shape.coordinates);
      }

      if (layer) {
        setupLayerHoverEvents(layer);
        drawnItems.value.addLayer(layer);
      }
    });
  } catch (error) {
    console.error('Error loading saved shapes:', error);
  }
}
</script>

<style>
@import 'leaflet/dist/leaflet.css';
@import 'leaflet-draw/dist/leaflet.draw.css';
@import '@geoman-io/leaflet-geoman-free/dist/leaflet-geoman.css';

.hover-card {
  padding: 8px;
  background-color: white;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
</style>