#!/usr/bin/env node
/**
 * AStockEveryDay 前端冒烟测试(CI / 本地 pre-commit 用)
 *
 * 使命:拦住"页面结构被改坏"这类 validate_data.py 管不到的问题——
 *   - home() 渲染后三个 tab 面板必须是 #app 的直接子节点(平级),不能互相嵌套
 *     (2026-08 真实事故:latest 面板少一个 </div> → history/backtest 面板被
 *     嵌套进 display:none 的 latest 面板,切换 tab 全部空白)
 *   - 全部 div 标签配对平衡
 *   - 渲染输出不含 undefined / [object Object] / NaN(数据-schema 错配)
 *   - escapeHtml 转义逻辑正确
 *
 * 原理:在 Node vm 中用最小 DOM stub 执行 index.html 的 app 脚本,
 *       用真实 data/*.json 渲染首页与每一期预测详情页,然后做结构断言。
 *       零第三方依赖(node>=18,自带 fetch 不需要——我们 stub 为本地文件读取)。
 *
 * 用法:  node scripts/smoke_test.mjs       # 退出码 0=通过, 1=失败
 */
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const errors = [];

const fail = (msg) => { errors.push(msg); };

/* ---------- 1. 提取 index.html 中的 app 脚本(最后一个内联 <script>) ---------- */
const html = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8');
const scriptBlocks = [...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)].map(m => m[1]);
const appScript = scriptBlocks[scriptBlocks.length - 1];
if (!appScript || !appScript.includes('init();')) {
  fail('未能从 index.html 提取 app 脚本');
  process.exitCode = 1;
  process.exit();
}

/* ---------- 2. 最小 DOM/fetch stub,让 app 脚本在 Node 里跑起来 ---------- */
const appEl = { innerHTML: '', style: {}, className: '', dataset: {} };

const fakeFetch = async (url) => {
  const p = path.join(ROOT, url);
  if (!fs.existsSync(p)) return { ok: false, json: async () => null };
  return { ok: true, json: async () => JSON.parse(fs.readFileSync(p, 'utf8')) };
};

const sandbox = {
  console,
  setTimeout,
  clearTimeout,
  Promise,
  JSON,
  Math,
  Date,
  String,
  Number,
  RegExp,
  fetch: fakeFetch,
  document: {
    querySelector: (sel) => (sel === '#app' ? appEl : null),
    querySelectorAll: () => [],
  },
  window: { addEventListener() {}, scrollTo() {} },
  location: { hash: '' },
  tailwind: {},
};
vm.createContext(sandbox);
vm.runInContext(appScript, sandbox, { filename: 'index.html' });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const waitApp = async (deadline = 5000) => {
  const t0 = Date.now();
  while (appEl.innerHTML === '' && Date.now() - t0 < deadline) await sleep(5);
  return appEl.innerHTML;
};

/* ---------- 3. 轻量 HTML 标签栈解析器(只关心配对与嵌套深度) ---------- */
const VOID_TAGS = new Set(['br', 'img', 'input', 'hr', 'meta', 'link', 'area', 'base', 'col', 'embed', 'source', 'track', 'wbr']);

function parseFragment(htmlText) {
  const stack = [];          // 当前未闭合标签栈(祖先链)
  const openTags = [];       // { name, attrs, depth: 开标签时祖先数 }
  const tokenRe = /<!--[\s\S]*?-->|<\/?[a-zA-Z][^>]*>/g;
  let m;
  while ((m = tokenRe.exec(htmlText))) {
    const tok = m[0];
    if (tok.startsWith('<!--')) continue;
    if (tok.startsWith('</')) {
      const name = tok.slice(2, -1).trim().toLowerCase().split(/\s/)[0];
      const top = stack[stack.length - 1];
      if (!top || top.name !== name) {
        fail(`HTML 结构:闭合 </${name}> 与栈顶 <${top ? top.name : '∅'}> 不匹配 (片段: ${tok.slice(0, 80)})`);
        return null;
      }
      top.closeDepth = stack.length - 1; // 闭合后剩余祖先数
      stack.pop();
    } else {
      const inner = tok.slice(1, -1);
      const selfClosing = /\/\s*$/.test(inner);
      const name = inner.trim().toLowerCase().split(/\s/)[0];
      const attrs = inner;
      const depth = stack.length; // 开标签前的祖先数 = 嵌套深度
      if (!selfClosing && !VOID_TAGS.has(name)) {
        stack.push({ name, attrs, depth, closeDepth: -1 });
      }
      openTags.push({ name, attrs, depth, selfClosing });
    }
  }
  if (stack.length > 0) {
    fail(`HTML 结构:有 ${stack.length} 个标签未闭合: ${stack.map(t => t.name).join(', ')}`);
    return null;
  }
  return { stack: openTags };
}

/* ---------- 4. 断言工具 ---------- */
const badRenderMarks = (text) => {
  const hits = [];
  if (text.includes('undefined')) hits.push('undefined');
  if (text.includes('[object Object]')) hits.push('[object Object]');
  if (text.includes('NaN')) hits.push('NaN');
  return hits;
};

function checkPanelStructure(frag) {
  const panels = frag.stack.filter(t => t.name === 'div' && t.attrs.includes('data-tab='));
  if (panels.length !== 3) return fail(`首页应恰好 3 个 tab 面板(div),实际 ${panels.length}`);
  const tabs = panels.map(p => (p.attrs.match(/data-tab="([^"]+)"/) || [])[1]);
  const expected = ['latest', 'history', 'backtest'];
  if (tabs.join(',') !== expected.join(',')) return fail(`tab 面板顺序/名称错误: ${tabs.join(',')}`);
  for (const p of panels) {
    if (p.depth !== 0) {
      fail(`面板 [${(p.attrs.match(/data-tab="([^"]+)"/) || [])[1]}] 嵌套深度为 ${p.depth},必须是 #app 直接子节点(平级兄弟)`);
    }
  }
  // 页脚(含免责声明)必须是平级兄弟,不能被面板吞进去
  const footers = frag.stack.filter(t => t.name === 'div' && t.attrs.includes('免责声明') === false && t.attrs.includes('text-center py-12'));
  if (footers.length !== 1 || footers[0].depth !== 0) {
    fail(`页脚应为 #app 直接子节点,当前 ${footers.length} 个,深度 ${footers[0] ? footers[0].depth : '∅'}`);
  }
}

/* ---------- 5. 执行检查 ---------- */
// 5.1 escapeHtml 单测
const escProbe = vm.runInContext('escapeHtml(\'<b>x</b> & "q" \\\'a\\\'\')', sandbox);
if (escProbe !== '&lt;b&gt;x&lt;/b&gt; &amp; &quot;q&quot; &#39;a&#39;') {
  fail(`escapeHtml 行为异常: 实际输出 ${JSON.stringify(escProbe)}`);
}

// 5.2 首页
const homeHtml = await waitApp();
if (homeHtml === '') fail('首页渲染超时/未产出 HTML(init 或 fetch stub 异常)');
if (homeHtml) {
  const frag = parseFragment(homeHtml);
  if (frag) checkPanelStructure(frag);
  const marks = badRenderMarks(homeHtml);
  if (marks.length) fail(`首页渲染输出包含异常标记: ${marks.join(', ')}`);
  if (!homeHtml.includes('最新一期')) fail('首页缺少「最新一期」tab 按钮');
  if (!homeHtml.includes('往期记录')) fail('首页缺少「往期记录」tab 按钮');
  if (!homeHtml.includes('回测数据')) fail('首页缺少「回测数据」tab 按钮');
}

// 5.3 每一期预测详情页
const dateFiles = fs.readdirSync(path.join(ROOT, 'data'))
  .filter(f => /^\d{8}\.json$/.test(f))
  .sort();
let rendered = 0;
for (const f of dateFiles) {
  const id = f.slice(0, 8);
  await sandbox.loadPrediction(id);
  const pageHtml = appEl.innerHTML;
  if (!pageHtml || pageHtml.includes('数据加载失败')) { fail(`${f}: 详情页渲染失败`); continue; }
  const frag = parseFragment(pageHtml);
  if (!frag) fail(`${f}: 详情页 div 配平失败`);
  const marks = badRenderMarks(pageHtml);
  if (marks.length) fail(`${f}: 渲染输出包含 ${marks.join(', ')}`);
  const d = JSON.parse(fs.readFileSync(path.join(ROOT, 'data', f), 'utf8'));
  if (d.title && !pageHtml.includes('涨停预测')) fail(`${f}: 详情页缺少标题区`);
  rendered++;
}

/* ---------- 6. 汇总 ---------- */
if (errors.length) {
  console.error(`\n❌ 冒烟测试失败 (${errors.length} 处):`);
  for (const e of errors) console.error(`   - ${e}`);
  console.error(`   已渲染详情页: ${rendered}/${dateFiles.length}`);
  process.exitCode = 1;
} else {
  console.log(`✅ 冒烟测试通过:首页结构正常(3 个平级 tab 面板),${rendered} 期详情页全部渲染无异常,escapeHtml 行为正确`);
}
