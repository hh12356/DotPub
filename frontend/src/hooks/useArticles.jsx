import { useState, useEffect, useCallback } from "react"
import { ArtGetAllAPI } from '@/apis/article'

const SIZE = 8

function useArticles(sort = 'latest') {
    const [articles, setArticles] = useState([])
    const [page, setPage]         = useState(1)
    const [hasMore, setHasMore]   = useState(true)
    const [loading, setLoading]   = useState(false)

    // sort 变了就整个重来
    useEffect(() => {
        let cancelled = false
        setLoading(true)
        ArtGetAllAPI({ page: 1, size: SIZE, sort })
            .then(res => {
                if (cancelled) return
                setArticles(res.data)
                setHasMore(res.has_more)
                setPage(1)
            })
            .finally(() => { if (!cancelled) setLoading(false) })
        // 旧请求晚回来时就知道自己过时了，不会覆盖新排序的结果
        return () => { cancelled = true }
    }, [sort])

    // 加载下一页
    const loadMore = useCallback(async () => {
        if (loading || !hasMore) return      //到底了就别再请求
        setLoading(true)
        try {
            const next = page + 1
            const res = await ArtGetAllAPI({ page: next, size: SIZE, sort })
            setArticles(prev => [...prev, ...res.data])   // 追加，不是替换
            setHasMore(res.has_more)
            setPage(next)
        } finally {
            setLoading(false)
        }
    }, [page, hasMore, loading, sort])

    return { articles, hasMore, loadMore, loading }
}

export { useArticles }