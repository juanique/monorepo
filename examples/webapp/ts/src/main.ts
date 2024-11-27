import { Chart, registerables } from 'chart.js';
import { formatNamePretty, NameStyle } from 'examples/ts/ts_library/formatting/formatting';

// Register components for Chart.js
Chart.register(...registerables);

// Create the chart
const ctx = document.getElementById('myChart') as HTMLCanvasElement;
const chart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: ['January', 'February', 'March', 'April', 'May', 'June'],
        datasets: [
            {
                label: formatNamePretty('Sales', NameStyle.Fancy),
                data: [10, 20, 15, 25, 30, 40],
                borderColor: 'rgba(255, 192, 192, 1)',
                borderWidth: 2,
                fill: false,
            },
        ],
    },
    options: {
        responsive: true,
        plugins: {
            legend: {
                display: true,
                position: 'top',
            },
        },
        scales: {
            x: {
                title: {
                    display: true,
                    text: 'Months',
                },
            },
            y: {
                title: {
                    display: true,
                    text: 'Sales (in $1000)',
                },
                beginAtZero: true,
            },
        },
    },
});

// Add an event listener to update chart data dynamically
const updateButton = document.getElementById('updateData');
updateButton?.addEventListener('click', () => {
    chart.data.datasets[0].data = chart.data.datasets[0].data.map(() =>
        Math.floor(Math.random() * 50)
    );
    chart.update();
});
