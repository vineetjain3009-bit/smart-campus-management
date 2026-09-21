async function loadDashboardChart() {
  const canvas = document.getElementById("attendance-chart");
  if (!canvas || !window.Chart) return;
  try {
    const response = await fetch("/api/analytics");
    const data = await response.json();
    new Chart(canvas, {
      type: "line",
      data: { labels: data.trend.map((item) => item.date.slice(5)), datasets: [{ label: "Attendance", data: data.trend.map((item) => item.percentage), borderColor: "#5261d8", backgroundColor: "rgba(82, 97, 216, .12)", fill: true, tension: .35, pointRadius: 2, pointHoverRadius: 5 }] },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { callbacks: { label: (context) => `${context.raw}% present` } } }, scales: { y: { min: 0, max: 100, ticks: { callback: (value) => `${value}%` }, grid: { color: "rgba(130, 140, 160, .13)" } }, x: { grid: { display: false } } } }
    });
  } catch (_) { canvas.closest(".chart-frame").innerHTML = '<div class="empty-state">Unable to load chart data.</div>'; }
}
loadDashboardChart();
