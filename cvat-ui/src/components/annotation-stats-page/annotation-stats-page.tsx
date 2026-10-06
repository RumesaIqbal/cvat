// Copyright (C) CVAT.ai Corporation
//
// SPDX-License-Identifier: MIT

import './styles.scss';

import React, { useEffect, useState } from 'react';
import notification from 'antd/lib/notification';
import { Row, Col } from 'antd/lib/grid';
import List from 'antd/lib/list';
import Statistic from 'antd/lib/statistic';
import Result from 'antd/lib/result';
import Alert from 'antd/lib/alert';
import Select from 'antd/lib/select';
import { useParams } from 'react-router';

import { getCore } from 'cvat-core-wrapper';
import GoBackButton from 'components/common/go-back-button';
import CVATLoadingSpinner from 'components/common/loading-spinner';
import AnnotationStatsChart from './annotation-stats-chart';
import { AnnotationGroupBy, AnnotationStats } from '.';

const core = getCore();

function AnnotationStatsPage(): JSX.Element {
    const { id } = useParams<{ id: string }>();
    const taskId = Number(id);
    const [stats, setStats] = useState<AnnotationStats | null>(null);
    const [fetching, setFetching] = useState(true);
    const [failed, setFailed] = useState(false);
    const [groupBy, setGroupBy] = useState<AnnotationGroupBy>('label');

    useEffect(() => {
        let mounted = true;

        setFetching(true);
        setFailed(false);
        setStats(null);

        core.server.request(`/api/tasks/${taskId}/annotation-stats`, {
            method: 'GET',
            params: { group_by: groupBy },
        })
            .then((response: { data: AnnotationStats }) => {
                if (mounted) {
                    setStats(response.data);
                }
            })
            .catch((error: unknown) => {
                if (mounted) {
                    setFailed(true);
                    notification.error({
                        message: 'Could not read annotation statistics for the task',
                        description: error instanceof Error ? error.message : '',
                    });
                }
            })
            .finally(() => {
                if (mounted) {
                    setFetching(false);
                }
            });

        return () => {
            mounted = false;
        };
    }, [taskId, groupBy]);

    return (
        <div className='cvat-annotation-stats-page'>
            <div className='cvat-annotation-stats-wrapper'>
                <Row justify='center'>
                    <Col span={22} xl={18} xxl={14} className='cvat-annotation-stats-top-bar'>
                        <GoBackButton />
                    </Col>
                </Row>
                <Row justify='center' className='cvat-annotation-stats-inner-wrapper'>
                    <Col span={22} xl={18} xxl={14} className='cvat-annotation-stats-inner'>
                        { fetching && <CVATLoadingSpinner /> }
                        { !fetching && failed && (
                            <Result
                                status='error'
                                title='Could not load annotation statistics'
                                subTitle='Check that the task exists and that you have access to it.'
                            />
                        ) }
                        { !fetching && !failed && stats && (
                            <>
                                <Row justify='space-between' className='cvat-annotation-stats-header'>
                                    <Col>
                                        <h1>Annotation statistics</h1>
                                    </Col>
                                    <Col>
                                        <Select
                                            className='cvat-annotation-stats-group-selector'
                                            value={groupBy}
                                            onChange={(value: AnnotationGroupBy) => setGroupBy(value)}
                                        >
                                            <Select.Option value='label'>by label</Select.Option>
                                            <Select.Option value='source'>by source</Select.Option>
                                        </Select>
                                    </Col>
                                </Row>
                                { stats.total === 0 && (
                                    <Alert
                                        type='info'
                                        showIcon
                                        message='This task does not have any annotations yet.'
                                    />
                                ) }
                                <Row justify='start' className='cvat-annotation-stats-total'>
                                    <Col>
                                        <Statistic title='Total annotations' value={stats.total} />
                                    </Col>
                                </Row>
                                <Row justify='start' className='cvat-annotation-stats-counts-header'>
                                    <Col>
                                        <h2>{groupBy === 'label' ? 'Counts per label' : 'Counts per source'}</h2>
                                    </Col>
                                </Row>
                                <Row justify='start'>
                                    <Col span={24} className='cvat-annotation-stats-counts'>
                                        <List
                                            bordered
                                            dataSource={stats.counts}
                                            renderItem={(item) => (
                                                <List.Item>
                                                    <span>{item.key}</span>
                                                    <span>{item.count}</span>
                                                </List.Item>
                                            )}
                                        />
                                    </Col>
                                </Row>
                                <Row justify='start' className='cvat-annotation-stats-chart-header'>
                                    <Col>
                                        <h2>Chart</h2>
                                    </Col>
                                </Row>
                                <Row justify='start'>
                                    <Col span={24}>
                                        <AnnotationStatsChart counts={stats.counts} />
                                    </Col>
                                </Row>
                            </>
                        ) }
                    </Col>
                </Row>
            </div>
        </div>
    );
}

export default React.memo(AnnotationStatsPage);
