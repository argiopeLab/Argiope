const content = document.getElementById('helpContent');
const form = document.getElementById('helpSearchForm');
const input = document.getElementById('helpSearchInput');
let matches = [];
let activeIndex = -1;
let lastQuery = '';

document.querySelectorAll('a[href^="#"]').forEach((link) => {
  link.addEventListener('click', (event) => {
    const target = document.querySelector(link.getAttribute('href'));
    if (!target) return;
    event.preventDefault();
    target.scrollIntoView({ behavior: 'smooth' });
    history.replaceState(null, '', link.getAttribute('href'));
  });
});

function clearHighlights() {
  content.querySelectorAll('mark.help-search-hit').forEach((mark) => {
    mark.replaceWith(document.createTextNode(mark.textContent));
  });
  content.normalize();
  matches = [];
  activeIndex = -1;
}

function highlight(query) {
  clearHighlights();
  if (!query) return;
  const escaped = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const regex = new RegExp(escaped, 'gi');
  const walker = document.createTreeWalker(content, NodeFilter.SHOW_TEXT, {
    acceptNode(node) {
      const parent = node.parentElement;
      return node.nodeValue.trim() && parent && !['SCRIPT', 'STYLE', 'MARK'].includes(parent.tagName)
        ? NodeFilter.FILTER_ACCEPT
        : NodeFilter.FILTER_REJECT;
    }
  });
  const nodes = [];
  while (walker.nextNode()) nodes.push(walker.currentNode);
  nodes.forEach((node) => {
    const found = [...node.nodeValue.matchAll(regex)];
    if (!found.length) return;
    const fragment = document.createDocumentFragment();
    let cursor = 0;
    found.forEach((result) => {
      fragment.append(node.nodeValue.slice(cursor, result.index));
      const mark = document.createElement('mark');
      mark.className = 'help-search-hit';
      mark.textContent = result[0];
      fragment.append(mark);
      matches.push(mark);
      cursor = result.index + result[0].length;
    });
    fragment.append(node.nodeValue.slice(cursor));
    node.replaceWith(fragment);
  });
}

form.addEventListener('submit', (event) => {
  event.preventDefault();
  const query = input.value.trim();
  if (!query) {
    clearHighlights();
    return;
  }
  if (query !== lastQuery) {
    highlight(query);
    lastQuery = query;
    activeIndex = 0;
  } else if (matches.length) {
    activeIndex = (activeIndex + 1) % matches.length;
  }
  content.querySelector('mark.active')?.classList.remove('active');
  const match = matches[activeIndex];
  if (match) {
    match.classList.add('active');
    match.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }
});

input.addEventListener('input', () => {
  if (!input.value.trim()) {
    lastQuery = '';
    clearHighlights();
  }
});
