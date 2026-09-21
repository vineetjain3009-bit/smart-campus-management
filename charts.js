const chartPalette = ["#5261d8", "#18a999", "#f0a44c", "#8a69d4", "#587a99", "#d96b8f"];
const getThemeColor = () => getComputedStyle(document.documentElement).getPropertyValue("--text").trim();
const baseOptions = (extra = {}) => ({ responsive: true, maintainAspectRatio: false, plugins: { legend: { labels: { color: getThemeColor(), usePointStyle: true, boxWidth: 9 } } }, ...extra });
const labeledData = (rows, labelKey, valueKey) => ({ labels: rows.map((item) => item[labelKey]), data: rows.map((item) => item[valueKey]) });

async function loadCharts() {
  if (!window.Chart) return;
  try {
    const response = await fetch("/api/analytics");
    const data = await response.json();
    const department = labeledData(data.departments, "department", "count");
    new Chart(document.getElementById("department-chart"), { type: "doughnut", data: { labels: department.labels, datasets: [{ data: department.data, backgroundColor: chartPalette, borderWidth: 0 }] }, options: baseOptions({ cutout: "64%" }) });
    const bands = labeledData(data.attendance_distribution, "band", "count");
    new Chart(document.getElementById("attendance-distribution-chart"), { type: "bar", data: { labels: bands.labels, datasets: [{ label: "Students", data: bands.data, backgroundColor: chartPalette.slice(0, bands.data.length), borderRadius: 6 }] }, options: baseOptions({ scales: { y: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: "rgba(130, 140, 160, .13)" } }, x: { grid: { display: false } } } }) });
    const assignment = labeledData(data.assignments, "status", "count");
    new Chart(document.getElementById("assignment-chart"), { type: "doughnut", data: { labels: assignment.labels, datasets: [{ data: assignment.data, backgroundColor: ["#f0a44c", "#18a999", "#e26d71"], borderWidth: 0 }] }, options: baseOptions({ cutout: "64%" }) });
    const performance = labeledData(data.student_performance, "name", "percentage");
    new Chart(document.getElementById("performance-chart"), { type: "bar", data: { labels: performance.labels, datasets: [{ label: "Attendance", data: performance.data, backgroundColor: "#5261d8", borderRadius: 6 }] }, options: baseOptions({ indexAxis: "y", scales: { x: { min: 0, max: 100, ticks: { callback: (value) => `${value}%` }, grid: { color: "rgba(130, 140, 160, .13)" } }, y: { grid: { display: false } } } }) });
    const trend = labeledData(data.trend, "date", "percentage");
    new Chart(document.getElementById("trend-chart"), { type: "line", data: { labels: trend.labels.map((value) => value.slice(5)), datasets: [{ label: "Attendance", data: trend.data, borderColor: "#18a999", backgroundColor: "rgba(24,169,153,.1)", fill: true, tension: .35, pointRadius: 2 }] }, options: baseOptions({ scales: { y: { min: 0, max: 100, ticks: { callback: (value) => `${value}%` }, grid: { color: "rgba(130, 140, 160, .13)" } }, x: { grid: { display: false } } } }) });
  } catch (_) { document.querySelectorAll(".chart-frame").forEach((frame) => frame.innerHTML = '<div class="empty-state">Unable to load chart data.</div>'); }
}
loadCharts();
