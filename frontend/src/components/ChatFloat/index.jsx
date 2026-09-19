import { useEffect, useRef, useState } from "react"
import { useLocation } from "react-router-dom"
import { Button, Drawer, FloatButton, Input, message } from "antd"
import { RobotOutlined, SendOutlined } from "@ant-design/icons"
import { ChatAPI } from "@/apis/chat"
import { getToken } from "@/utils/token"
import "./index.scss"

const clamp = (v, min, max) => Math.min(Math.max(v, min), max)

const ChatFloat = () => {
    const [open, setOpen] = useState(false)
    // [{role:'user'|'assistant', content}]
    const [msgs, setMsgs] = useState([])
    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(false)
    //{right, bottom}，null 表示还在默认的右下角
    const [pos, setPos] = useState(null)

    //当前文章id
    const artId = Number(useLocation().pathname.match(/^\/article\/(\d+)/)?.[1]) || null

    const listRef = useRef(null)
    const dragRef = useRef(null)
    //拖动过就不算点击，否则松手会顺手把抽屉打开
    const movedRef = useRef(false)

    //拖动逻辑
    const onDragStart = e => {
        const rect = e.currentTarget.getBoundingClientRect()
        dragRef.current = {
            offsetX: e.clientX - rect.left,
            offsetY: e.clientY - rect.top,
            w: rect.width,
            h: rect.height,
        }
        movedRef.current = false
        e.currentTarget.setPointerCapture(e.pointerId)
    }

    const onDragMove = e => {
        const d = dragRef.current
        if (!d) return
        movedRef.current = true
        setPos({
            right: clamp(window.innerWidth - e.clientX - d.offsetX, 0, window.innerWidth - d.w),
            bottom: clamp(window.innerHeight - e.clientY - d.offsetY, 0, window.innerHeight - d.h),
        })
    }

    const onDragEnd = e => {
        if (!dragRef.current) return
        dragRef.current = null
        e.currentTarget.releasePointerCapture(e.pointerId)
    }

    //使对话框滚到最底部
    useEffect(() => {
        const el = listRef.current
        if (el) el.scrollTop = el.scrollHeight
    }, [msgs, loading])

    const onSend = async () => {
        //trim删掉首尾空格
        const question = input.trim()
        if (!question || loading) return

        //发出去的历史是这一句之前的内容，不含本轮
        const history = msgs
        setMsgs([...history, { role: 'user', content: question }])

        setInput('')
        setLoading(true)
        try {
            const res = await ChatAPI({ question, art_id: artId, history })
            setMsgs(prev => [...prev, { role: 'assistant', content: res.data.answer }])
        }
        catch (e) {
            //失败就把这一句撤回输入框
            setMsgs(prev => prev.slice(0, -1))//删掉最近一条记录
            setInput(question)
            message.error(e.response?.data?.detail?.msg || "请求失败，请稍后重试")
        }
        finally {
            setLoading(false)
        }
    }

    if (!getToken()) return null

    return (
        <>
            <FloatButton
                icon={<RobotOutlined />}
                type="primary"
                style={{
                    ...(pos || {}),
                    touchAction: 'none',
                    userSelect: 'none',
                    cursor: 'grab',
                    transition: 'none',
                }}
                //拖动
                onPointerDown={onDragStart}
                onPointerMove={onDragMove}
                onPointerUp={onDragEnd}
                onPointerCancel={onDragEnd}
                onClick={() => { if (!movedRef.current) setOpen(true) }}
            />
            <Drawer
                title="Dot"
                placement="right"
                size={750}
                open={open}
                onClose={() => setOpen(false)}
                styles={{ body: { display: 'flex', flexDirection: 'column', padding: 16 } }}
            >
                <div className="chat-list" ref={listRef}>
                    {/* 新对话时展示 */}
                    {msgs.length === 0 &&
                        <p className="chat-empty">
                            {artId ? '我是 Dot。问我这篇在讲什么，或者别的技术问题' : '我是 Dot，有技术问题都可以问我'}
                        </p>
                    }
                    {msgs.map((m, i) => (
                        <div key={i} className={`chat-msg chat-msg-${m.role}`}>{m.content}</div>
                    ))}
                    {loading && <div className="chat-msg chat-msg-assistant">思考中…</div>}
                </div>
                <div className="chat-input">
                    <Input.TextArea
                        value={input}
                        onChange={e => setInput(e.target.value)}
                        placeholder="问 Dot 点什么…"
                        autoSize={{ minRows: 1, maxRows: 4 }}
                        maxLength={500}
                        onPressEnter={e => { e.preventDefault(); onSend() }}
                    />
                    <Button
                        type="primary"
                        icon={<SendOutlined />}
                        loading={loading}
                        disabled={!input.trim()}
                        onClick={onSend}
                    />
                </div>
            </Drawer>
        </>
    )
}

export default ChatFloat
