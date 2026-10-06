// Copyright (C) CVAT.ai Corporation
//
// SPDX-License-Identifier: MIT

import React from 'react';
import { Bar } from 'react-chartjs-2';
import {
    BarElement,
    CategoryScale,
    Chart as ChartJS,
    ChartData,
    ChartOptions,
    Legend,
    LinearScale,
    Tooltip,
} from 'chart.js';

import { AnnotationCount } from '.';

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend);

interface Props {
    counts: AnnotationCount[];
}

function AnnotationStatsChart({ counts }: Props): JSX.Element {
    const data: ChartData<'bar'> = {
        labels: counts.map((item: AnnotationCount) => item.key),
        datasets: [
            {
                label: 'Annotations',
                data: counts.map((item: AnnotationCount) => item.count),
                backgroundColor: 'rgba(54, 162, 235, 0.6)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1,
            },
        ],
    };

    const options: ChartOptions<'bar'> = {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false },
        },
        scales: {
            x: {
                beginAtZero: true,
                title: { display: true, text: 'Annotations' },
            },
            y: {
                ticks: { autoSkip: false },
            },
        },
    };

    // Give every label its own readable row instead of cramming all
    // categories into a fixed-height container (which makes the axis labels
    // overlap). The page container scrolls for long label lists.
    const chartHeight = Math.max(320, counts.length * 24);

    return (
        <div className='cvat-annotation-stats-chart' style={{ height: `${chartHeight}px` }}>
            <Bar data={data} options={options} />
        </div>
    );
}

export default React.memo(AnnotationStatsChart);
