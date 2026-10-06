// Copyright (C) CVAT.ai Corporation
//
// SPDX-License-Identifier: MIT

export type AnnotationGroupBy = 'label' | 'source';

export type AnnotationCount = {
    key: string;
    count: number;
};

export type AnnotationStats = {
    task: number;
    group_by: AnnotationGroupBy;
    total: number;
    counts: AnnotationCount[];
};
