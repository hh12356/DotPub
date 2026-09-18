import { AdminGetData } from "@/apis/admin"
import { Flex, Result, Segmented, Spin, Statistic, Typography } from "antd"
import * as echarts from "echarts"
import { useEffect, useMemo, useRef, useState } from "react"

const TOTALS = [
    { key: 'user',    label: '用户' },
    { key: 'article', label: '文章' },
    { key: 'comment', label: '评论' },
    { key: 'like',    label: '点赞' },
    { key: 'star',    label: '收藏' },
]

const METRICS = [
    { key: 'like',    label: '点赞', list: 'top_liked',     field: 'like_count' },
    { key: 'star',    label: '收藏', list: 'top_starred',   field: 'star_count' },
    { key: 'comment', label: '评论', list: 'top_commented', field: 'comment_count' },
]

const Chart = ({ option, height = 320 }) => {
    const ref = useRef(null)

    useEffect(() => {
        const chart = echarts.init(ref.current)
        chart.setOption(option)
        //宽度是 100%，窗口一变就得让 echarts 重新量一次，否则画布不跟着走
        const onResize = () => chart.resize()
        window.addEventListener('resize', onResize)
        return () => {
            window.removeEventListener('resize', onResize)
            chart.dispose()
        }
    }, [option])

    return <div ref={ref} style={{ width: '100%', height }} />
}

//横向条形图：类目轴在 y 上是从下往上画的，所以先反转，让第一名落在最上面
//showName 关掉的是轴标签，名字还在 data 里，鼠标移上去 tooltip 照样能看
const barOption = (pairs, color, showName = true) => {
    const rows = [...pairs].reverse()
    return {
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
        grid: { left: 8, right: 32, containLabel: true },
        xAxis: { type: 'value', minInterval: 1 },
        yAxis: { type: 'category', data: rows.map(r => r.name), axisLabel: { show: showName } },
        series: [{ type: 'bar', data: rows.map(r => r.value), itemStyle: { color } }],
    }
}

const Admin = () => {
    const [data, setData] = useState(null)
    const [error, setError] = useState(null)
    const [metric, setMetric] = useState('like')

    useEffect(() => {
        const fetchData = async () => {
            try {
                const res = await AdminGetData()
                setData(res.data)
            }
            catch (e) {
                setError(e.response?.status === 403 ? '403' : '500')
            }
        }
        fetchData()
    }, [])

    const trend = data?.trend
    const m = METRICS.find(x => x.key === metric)

    //option 必须 memo：Chart 的 effect 依赖它，每次渲染都换新对象
    //就会 dispose 再 init 一次，图表会闪
    const trendOption = useMemo(() => data && {
        tooltip: { trigger: 'axis' },
        legend: { data: ['文章', '用户'] },
        grid: { left: 8, right: 32, containLabel: true },
        xAxis: { type: 'category', boundaryGap: false, data: trend.dates },
        //minInterval:1 —— 这些单位是"篇/人"，不是连续量，别让 y 轴冒出 0.5
        yAxis: { type: 'value', minInterval: 1 },
        series: [
            { name: '文章', type: 'line', smooth: true, data: trend.articles },
            { name: '用户', type: 'line', smooth: true, data: trend.users },
        ],
    }, [data])

    const topOption = useMemo(
        () => data && barOption(
            (data[m.list] ?? []).map(r => ({ name: r.art_title, value: r[m.field] })),
            '#1677ff',
            false
        ),
        [data, m]
    )

    const userOption = useMemo(
        () => data && barOption(
            data.active_users.map(u => ({ name: u.user_name, value: u.art_count })),
            '#52c41a'
        ),
        [data]
    )

    if (error) return (
        <Result
            status={error === '403' ? '403' : 'error'}
            title={error === '403' ? '无权访问' : '服务器出错了'}
            style={{ marginTop: 80 }}
        />
    )

    if (!data) return (
        <Flex justify="center" style={{ marginTop: 120 }}>
            <Spin size="large" />
        </Flex>
    )

    return (
        <div style={{ width: '85vw', margin: '24px auto' }}>
            <Typography.Title level={3} style={{ marginTop: 0 }}>数据看板</Typography.Title>

            <Flex justify="space-around" style={{ marginBottom: 32 }}>
                {TOTALS.map(t => (
                    <Statistic key={t.key} title={t.label} value={data.totals[t.key]} />
                ))}
            </Flex>

            <Typography.Title level={4}>近 14 天趋势</Typography.Title>
            <Chart option={trendOption} />

            <Flex align="center" gap={16} style={{ marginTop: 32 }}>
                <Typography.Title level={4} style={{ margin: 0 }}>人气榜</Typography.Title>
                <Segmented
                    value={metric}
                    onChange={setMetric}
                    options={METRICS.map(x => ({ label: x.label, value: x.key }))}
                />
            </Flex>
            <Chart option={topOption} />

            <Typography.Title level={4} style={{ marginTop: 32 }}>发文最多的用户</Typography.Title>
            <Chart option={userOption} />
        </div>
    )
}

export default Admin
