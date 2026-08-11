#!/usr/bin/env node
/**
 * AStockEveryDay 前端冒烟测试(CI / 本地 pre-commit 用)
 *
 * 使命:拦住"页面结构被改坏"这类 validate_data.py 管不到的问题——
 *   - home() 渲染后三个 tab 面板必须是 #app 的直接子节点(平级),不能互相嵌套
 *     (2026-08 真实事故:latest 面板少一个 </div> → history/backtest 面板被
 *     嵌套进 display:none 的 latest 面板,切换 tab 全部空白)
 *   - 点击 tab 按钮后,对应面板显示、其余隐藏(行为级回归)
 *   - 渲染输出不含 undefined / [object Object] / NaN(数据-schema 错配)
 *   - h() DOM 构建助手:文本自动转义、富文本走 html 通道
 *   - 回测 tab 包含统计总览 + 按日期汇总 + 个股明细
 *
 * 原理:在 Node vm 中用最小 DOM stub(document.createElement/textNode + 选择器)
 *       执行 index.html 的 app 脚本,用真实 data/*.json 渲染首页、执行 tab 点击,
 *       并渲染每一期预测详情页,然后对 DOM 树直接断言。
 *       零第三方依赖(node>=18)。
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

/* ---------- 0. 最小 DOM stub ---------- */
class El {
  constructor(tag) {
    this.tagName = String(tag).toUpperCase();
    this.children = [];
    this.parent = null;
    this.attributes = {};
    // 模拟 CSSStyleDeclaration:未设置的样式属性读取为 ''(与浏览器一致)
    this.style = new Proxy({}, {
      get: (t, k) => (k in t ? t[k] : ''),
      set: (t, k, v) => { t[k] = v; return true; },
    });
    this.dataset = {};
    this.className = '';
    this._text = '';
    this._rich = null;
    this.listeners = {};
  }
  appendChild(c) {
    if (c === this) throw new Error('cannot append self');
    if (c.parent) c.parent.removeChild(c);
    c.parent = this;
    this.children.push(c);
    return c;
  }
  removeChild(c) {
    const i = this.children.indexOf(c);
    if (i >= 0) { this.children.splice(i, 1); c.parent = null; }
  }
  replaceChildren(...cs) {
    while (this.children.length) this.removeChild(this.children[0]);
    for (const c of cs.flat()) {
      if (c === null || c === undefined || c === false) continue;
      this.appendChild(c);
    }
  }
  setAttribute(k, v) {
    this.attributes[k] = String(v);
    if (k.startsWith('data-')) this.dataset[k.slice(5)] = String(v);
  }
  getAttribute(k) {
    return Object.prototype.hasOwnProperty.call(this.attributes, k) ? this.attributes[k] : null;
  }
  addEventListener(type, fn) { (this.listeners[type] = this.listeners[type] || []).push(fn); }
  click() { (this.listeners.click || []).forEach(fn => fn.call(this)); }
  set innerHTML(v) { this._rich = String(v); this._text = ''; this.children = []; }
  get innerHTML() { return this._rich || ''; }
  set textContent(v) { this._text = String(v); this.children = []; }
  get textContent() {
    return this._text + this.children.map(c => c.textContent).join('') + (this._rich || '');
  }
}

class TextNode {
  constructor(t) { this.text = String(t); this.parent = null; }
  get textContent() { return this.text; }
}

// 选择器子集: #id | .cls | tag | [attr="v"] 及组合
function matchSelector(el, sel) {
  sel = sel.trim();
  let attrK = null, attrV = null;
  const am = sel.match(/\[([\w-]+)="([^"]*)"\]\s*$/);
  if (am) { attrK = am[1]; attrV = am[2]; sel = sel.slice(0, am.index); }
  const im = sel.match(/^#([\w-]+)/);
  if (im) {
    if (el.getAttribute('id') !== im[1]) return false;
    sel = sel.slice(im[0].length);
  }
  const tm = sel.match(/^[a-zA-Z][\w-]*/);
  let tag = null;
  if (tm) { tag = tm[0].toLowerCase(); sel = sel.slice(tm[0].length); }
  const classes = [...sel.matchAll(/\.([\w-]+)/g)].map(m => m[1]);
  if (tag && el.tagName.toLowerCase() !== tag) return false;
  if (attrK !== null && el.getAttribute(attrK) !== attrV) return false;
  const own = (el.className || '').split(/\s+/);
  for (const c of classes) if (!own.includes(c)) return false;
  return true;
}

function collectMatches(root, sel, out) {
  for (const c of root.children) {
    if (!c.children) continue; // TextNode 无子树
    if (matchSelector(c, sel)) out.push(c);
    collectMatches(c, sel, out);
  }
  return out;
}

const appEl = new El('div');
appEl.attributes.id = 'app';

const documentStub = {
  querySelector: (sel) => (sel === '#app' ? appEl : collectMatches(appEl, sel, [])[0] || null),
  querySelectorAll: (sel) => collectMatches(appEl, sel, []),
  createElement: (tag) => new El(tag),
  createTextNode: (t) => new TextNode(t),
};

/* ---------- 1. 提取 index.html 中的 app 脚本(最后一个内联 <script>) ---------- */
const html = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8');
const scriptBlocks = [...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)].map(m => m[1]);
const appScript = scriptBlocks[scriptBlocks.length - 1];
if (!appScript || !appScript.includes('init();')) {
  fail('未能从 index.html 提取 app 脚本');
  process.exitCode = 1;
  process.exit();
}

/* ---------- 2. 沙箱:让 app 脚本在 Node 里跑起来 ---------- */
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
  document: documentStub,
  window: { addEventListener() {}, scrollTo() {} },
  location: { hash: '' },
  tailwind: {},
};
vm.createContext(sandbox);
vm.runInContext(appScript, sandbox, { filename: 'index.html' });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const waitApp = async (deadline = 5000) => {
  const t0 = Date.now();
  while (appEl.textContent === '' && Date.now() - t0 < deadline) await sleep(5);
  return appEl.textContent;
};

/* ---------- 3. 断言工具 ---------- */
const badRenderMarks = (text) => {
  const hits = [];
  if (text.includes('undefined')) hits.push('undefined');
  if (text.includes('[object Object]')) hits.push('[object Object]');
  if (text.includes('NaN')) hits.push('NaN');
  return hits;
};

/* ---------- 4. 执行检查 ---------- */
// 4.1 h() 助手单测:文本节点自动转义(按字面量输出,不解析 HTML)、富文本走 html 通道
const hProbe = vm.runInContext(`
  (() => {
    const probe = h('div', {class:'x'}, 'a<b>&"\\'');
    const textSafe = probe.children.length === 1
      && probe.children[0].textContent === 'a<b>&"\\'';
    const rich = h('p', {html:'<b>ok</b>'});
    return textSafe && rich.innerHTML === '<b>ok</b>' && rich.children.length === 0;
  })()
`, sandbox);
if (!hProbe) fail('h() 助手行为异常(文本应转义、富文本应走 html 通道)');

// 4.2 首页:结构 + tab 行为 + 回测统计
const homeText = await waitApp();
if (homeText === '') fail('首页渲染超时/未产出内容(init 或 fetch stub 异常)');

const appChildren = [...appEl.children];
const panels = appChildren.filter(c => c.getAttribute('data-tab') !== null);
const tabBtns = documentStub.querySelectorAll('.tab-btn');

if (panels.length !== 3) fail(`首页应恰好 3 个 tab 面板,实际 ${panels.length}`);
const tabNames = panels.map(p => p.getAttribute('data-tab'));
if (tabNames.join(',') !== 'latest,history,backtest') fail(`tab 面板顺序/名称错误: ${tabNames.join(',')}`);
for (const p of panels) {
  if (p.parent !== appEl) fail(`面板 [${p.getAttribute('data-tab')}] 不是 #app 直接子节点(平级兄弟),已被嵌套`);
}
const footer = appChildren.find(c => (c.className || '').includes('text-center py-12'));
if (!footer || footer.parent !== appEl) fail('页脚应为 #app 直接子节点');
if (tabBtns.length !== 3) fail(`tab 按钮应为 3 个,实际 ${tabBtns.length}`);

for (const mk of badRenderMarks(appEl.textContent)) fail(`首页渲染输出包含异常标记: ${mk}`);

// 4.2.1 tab 行为级回归(原始 bug 类型:切换后内容不可见)
const pnl = (t) => documentStub.querySelector(`.tab-panel[data-tab="${t}"]`);
const btn = (t) => tabBtns.find(b => b.getAttribute('data-tab') === t);
if (!pnl('latest') || !pnl('history') || !pnl('backtest') || !btn('history') || !btn('backtest')) {
  fail('tab 面板/按钮查询失败');
} else {
  if (pnl('latest').style.display !== '') fail('初始 latest 面板应显示');
  btn('history').click();
  if (pnl('history').style.display === 'none' || pnl('history').parent !== appEl) fail('切到往期记录后 history 面板应显示且平级');
  if (pnl('latest').style.display !== 'none') fail('切到往期记录后 latest 面板应隐藏');
  if (pnl('backtest').style.display !== 'none') fail('切到往期记录后 backtest 面板应隐藏');

  btn('backtest').click();
  const btText = pnl('backtest').textContent;
  if (!btText.includes('回测总览')) fail('回测 tab 缺少「回测总览」统计');
  if (!btText.includes('按预测日期汇总')) fail('回测 tab 缺少「按预测日期汇总」');
  if (!btText.includes('个股回测明细')) fail('回测 tab 缺少「个股回测明细」');
  if (!btText.includes('/205')) fail('回测总览缺少 盈利/总 计数(应为 x/205)');
  if (!btText.includes('胜率')) fail('回测总览缺少胜率');
  if (pnl('backtest').style.display === 'none') fail('切到回测后 backtest 面板应显示');

  btn('latest').click();
  if (pnl('latest').style.display !== '') fail('切回最新一期后 latest 面板应显示');
  if (pnl('history').style.display !== 'none') fail('切回最新一期后 history 面板应隐藏');
  if (pnl('backtest').style.display !== 'none') fail('切回最新一期后 backtest 面板应隐藏');
}

// 4.3 每一期预测详情页
const dateFiles = fs.readdirSync(path.join(ROOT, 'data'))
  .filter(f => /^\d{8}\.json$/.test(f))
  .sort();
let rendered = 0;
for (const f of dateFiles) {
  const id = f.slice(0, 8);
  await sandbox.loadPrediction(id);
  const pageText = appEl.textContent;
  if (!pageText || pageText.includes('数据加载失败')) { fail(`${f}: 详情页渲染失败`); continue; }
  if (!pageText.includes('涨停预测')) fail(`${f}: 详情页缺少标题区`);
  for (const mk of badRenderMarks(pageText)) fail(`${f}: 渲染输出包含 ${mk}`);
  rendered++;
}

/* ---------- 5. 汇总 ---------- */
if (errors.length) {
  console.error(`\n❌ 冒烟测试失败 (${errors.length} 处):`);
  for (const e of errors) console.error(`   - ${e}`);
  console.error(`   已渲染详情页: ${rendered}/${dateFiles.length}`);
  process.exitCode = 1;
} else {
  console.log(`✅ 冒烟测试通过:首页 3 平级面板 + tab 切换行为 + 回测统计,${rendered} 期详情页全部渲染无异常,h() 转义正确`);
}
