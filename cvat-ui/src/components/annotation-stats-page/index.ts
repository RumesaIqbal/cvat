// Copyright (C) CVAT.ai Corporation
//
// SPDX-License-Identifier: MIT

export type AnnotationCount = {
    key: string;
    count: number;
};

export type AnnotationStats = {
    task: number;
    group_by: string;
    total: number;
    counts: AnnotationCount[];
};
