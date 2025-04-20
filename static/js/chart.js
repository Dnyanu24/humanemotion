const ctx = document.getElementById('emotionChart').getContext('2d');
let emotionChart;

async function fetchEmotionData() {
    const response = await fetch('/api/emotion-data');
    return await response.json();
}

function fetchEmotionData() {
    // Fetch the emotion data from the server
    fetch('/process_frame', {
        method: 'POST',
        body: new FormData(document.getElementById('frameForm'))
    })
    .then(response => response.json())
    .then(data => {
        console.log(data);
        // Call the function to update the graph with new data
        updateGraph(data.probabilities);
    })
    .catch(error => console.error('Error:', error));
}

function updateGraph(emotionProbabilities) {
    // Use the probabilities to update your graph
    var data = {
        labels: Object.keys(emotionProbabilities),
        datasets: [{
            label: 'Emotion Probabilities',
            data: Object.values(emotionProbabilities),
            backgroundColor: ['#FF9999', '#66B3FF', '#99FF99', '#FFCC99', '#FF99FF', '#FFFF99', '#FF6666'],
            borderColor: '#fff',
            borderWidth: 1
        }]
    };

    // Update the chart using Chart.js or any other charting library
    var ctx = document.getElementById('emotionChart').getContext('2d');
    var emotionChart = new Chart(ctx, {
        type: 'bar', // Choose chart type (e.g., bar, line, etc.)
        data: data,
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// Set interval to update the graph every few seconds
setInterval(fetchEmotionData, 5000);  // Update every 5 seconds

async function updateChart() {
    const data = await fetchEmotionData();
    const labels = Object.keys(data);
    const counts = Object.values(data);

    if (!emotionChart) {
        emotionChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Emotion Count',
                    data: counts,
                    backgroundColor: 'rgba(75, 192, 192, 0.6)',
                }]
            },
            options: {
                responsive: true,
                animation: { duration: 500 },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    } else {
        emotionChart.data.labels = labels;
        emotionChart.data.datasets[0].data = counts;
        emotionChart.update();
    }
}

setInterval(updateChart, 3000); // Update every 3 seconds
updateChart(); // Initial call
const emotionChart = document.getElementById('emotionChart');
const chart = new Chart(emotionChart, {
  type: 'bar',
  data: {
    labels: ['Happy', 'Sad', 'Angry', 'Surprised'],
    datasets: [{
      label: 'Live Emotions',
      data: [35, 25, 15, 25],
      backgroundColor: ['#34D399', '#3B82F6', '#EF4444', '#FBBF24'],
    }]
  },
  options: {
    responsive: true,
    animation: {
      duration: 1000
    }
  }
});

// Optional: simulate live update every 5s
setInterval(() => {
  chart.data.datasets[0].data = chart.data.datasets[0].data.map(() => Math.floor(Math.random() * 100));
  chart.update();
}, 5000);
