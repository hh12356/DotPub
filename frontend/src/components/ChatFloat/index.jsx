import { useEffect, useRef, useState } from "react"
import { Button, Drawer, FloatButton, Input, message } from "antd"
import { RobotOutlined, SendOutlined } from "@ant-design/icons"
import DOMPurify from "dompurify"
import { marked } from "marked"
import { ChatStream } from "@/apis/chat"
import { getToken, getUserId } from "@/utils/token"
import "./index.scss"

const POS_KEY = 'chat_pos'

//当前界面：文章 or 首页
const msgsKey = artId => `chat_msgs_${getUserId()}_${artId ?? 'home'}`

//读取历史对话记录，存在sessionStorage
const readMsgs = artId => {
    try {
        const m = JSON.parse(sessionStorage.getItem(msgsKey(artId)))
        return Array.isArray(m) ? m : []
    } catch {
        return []
    }
}

//按钮宽度，用于把存下来的位置夹回视口内（antd FloatButton 默认 40）
const BTN = 40


const clamp = (v, min, max) => Math.min(Math.max(v, min), max)
//读取悬浮按钮位置
const readPos = () => {
    try {
        const p = JSON.parse(sessionStorage.getItem(POS_KEY))
        //检验数据合法性：必须是数字
        if (typeof p?.right !== 'number' || typeof p?.bottom !== 'number') return null
        //窗口被缩小过的话，原样恢复会让按钮停在视口外，拖都拖不回来
        return {
            right: clamp(p.right, 0, window.innerWidth - BTN),
            bottom: clamp(p.bottom, 0, window.innerHeight - BTN),
        }
    } catch {
        return null
    }
}

//回答里的外链要新开标签，否则一点就离开站点，回来还得重新拉开抽屉。
//这是 DOMPurify 的全局钩子，文章正文那条 sanitize 也会走这里，行为一致
DOMPurify.addHook('afterSanitizeAttributes', node => {
    //只处理<a>超链接标签
    if (node.tagName === 'A') {
        //新增标签页跳转:target="_blank"
        node.setAttribute('target', '_blank')
        //配套target="_blank"的安全属性
        node.setAttribute('rel', 'noopener noreferrer')
    }
})

//Dot 回的是 markdown；用户自己敲的按纯文本显示，保住换行
const renderBody = m => {
    if (!m.content) return '思考中…'
    if (m.role !== 'assistant') return m.content
    //marked.prase()将md转换为html
    //sanitize做html消毒
    //dangerouslySetInnerHTML注入html，消毒必须紧贴 dangerouslySetInnerHTML
    return <div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(marked.parse(m.content)) }} />
}

const ChatFloat = ({ artId }) => {
    const [open, setOpen] = useState(false)
    // [{role:'user'|'assistant', content}]
    const [msgs, setMsgs] = useState(() => readMsgs(artId))
    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(false)
    //{right, bottom}，null 表示还在默认的右下角
    const [pos, setPos] = useState(readPos)

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
        const next = {
            right: clamp(window.innerWidth - e.clientX - d.offsetX, 0, window.innerWidth - d.w),
            bottom: clamp(window.innerHeight - e.clientY - d.offsetY, 0, window.innerHeight - d.h),
        }
        //存一份在 dragRef 上：state 可能还没提交，松手时读到的是上一帧的值
        d.last = next
        setPos(next)
    }

    const onDragEnd = e => {
        const d = dragRef.current
        if (!d) return
        if (d.last) sessionStorage.setItem(POS_KEY, JSON.stringify(d.last))
        dragRef.current = null
        e.currentTarget.releasePointerCapture(e.pointerId)
    }

    //使对话框滚到最底部
    useEffect(() => {
        const el = listRef.current
        if (el) el.scrollTop = el.scrollHeight
    }, [msgs, loading])

    //流式期间每来一个字 msgs 都会变，攒到这一轮结束再写一次就够
    useEffect(() => {
        if (!loading) sessionStorage.setItem(msgsKey(artId), JSON.stringify(msgs))
    }, [msgs, loading, artId])

    const onSend = async () => {
        const question = input.trim()
        if (!question || loading) return

        const history = msgs
        //先占位：用户这句 + 一个空的 Dot 气泡
        setMsgs([...history, { role: 'user', content: question }, { role: 'assistant', content: '' }])
        setInput('')
        setLoading(true)

        let got = ''
        try {
            await ChatStream({ question, art_id: artId, history }, t => {
                got += t
                setMsgs(prev => {
                    const last = prev[prev.length - 1]
                    return [...prev.slice(0, -1), { ...last, content: last.content + t }]
                })
            })
        }
        catch (e) {
            message.error(e.message)
            //一个字都没吐出来才整轮撤回、问题还回输入框；吐了一半就留着，别让答案凭空消失
            if (!got) {
                setMsgs(prev => prev.slice(0, -2))
                setInput(question)
            }
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
                        <div key={i} className={`chat-msg chat-msg-${m.role}`}>{renderBody(m)}</div>
                    ))}
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
