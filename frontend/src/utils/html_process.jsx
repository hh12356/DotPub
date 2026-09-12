
// 正文是 HTML，取纯文本的第一行做摘要
const firstLine = (html) => {
    // 块级标签先换成换行，否则多个段落会粘成一行
    const withBreaks = (html || '').replace(/<\/(p|div|li|h[1-6])>|<br\s*\/?>/gi, '\n');
    // 交给浏览器解析，实体（&nbsp; &amp; 等）会被自动解码
    const doc = new DOMParser().parseFromString(withBreaks, 'text/html');
    return (doc.body.textContent || '')
        .split('\n')
        .map((line) => line.trim())
        .find(Boolean) || '';
};


export {firstLine}