const DEFAULT_PAGE = "wiki/README.md";

const NAV_SECTIONS = [
  {
    title: "General Info",
    items: [
      { label: "Home", path: "wiki/README.md" },
      { label: "First-Run Setup", path: "wiki/First-Run-Setup.md" },
      { label: "Vault Vs Project", path: "wiki/Vault-Vs-Project.md" },
    ],
  },
  {
    title: "Importing Mods",
    items: [
      { label: "Manual Import", path: "wiki/Manual-Import.md" },
      { label: "One-Click Imports", path: "wiki/One-Click-Imports.md" },
      {
        label: "Slippi Safety",
        path: "wiki/Slippi-Safety.md",
        children: [
          { label: "Validation Internals", path: "wiki/Slippi-Validation-Internals.md" },
        ],
      },
    ],
  },
  {
    title: "Mod Types",
    items: [
      {
        label: "Character Mods",
        path: "wiki/Character-Mod-Workflow.md",
        children: [
          { label: "Ice Climbers Pairing", path: "wiki/Ice-Climbers-Pairing.md" },
          { label: "CSPs And Poses", path: "wiki/CSP-And-Pose-Workflow.md" },
        ],
      },
      {
        label: "Stage Mods",
        path: "wiki/Stage-Mod-Workflow.md",
      },
      {
        label: "Effect Mods",
        path: "wiki/Extras-And-Effects-Workflow.md",
        children: [
          { label: "Fox And Falco Shared Effects", path: "wiki/Fox-And-Falco-Shared-Extras.md" },
        ],
      },
    ],
  },
  {
    title: "Build And Sharing",
    items: [
      { label: "Vault Backup And Restore", path: "wiki/Vault-And-Distribution-Workflow.md" },
      { label: "CSP Compression", path: "wiki/CSP-Compression.md" },
      { label: "Patches", path: "wiki/Patches.md" },
      { label: "Texture Pack Mode", path: "wiki/Texture-Pack-Mode.md" },
    ],
  },
  {
    title: "Reference",
    items: [
      {
        label: "Melee Files Reference",
        path: "docs/new-414/Melee-Files.md",
      },
      {
        label: "Effect Offsets Reference",
        path: "docs/color-effects-reference/Effect-Offsets-Reference.md",
      },
    ],
  },
];

const navElement = document.getElementById("nav");
const pageTitleElement = document.getElementById("page-title");
const pagePathElement = document.getElementById("page-path");
const pageContentElement = document.getElementById("page-content");

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function slugify(value) {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, "")
    .trim()
    .replace(/\s+/g, "-");
}

function parseRoute() {
  const raw = window.location.hash.replace(/^#/, "");
  return raw ? decodeURIComponent(raw) : DEFAULT_PAGE;
}

function buildHash(path) {
  return `#${encodeURI(path)}`;
}

function buildFileUrl(path) {
  const encodedPath = path
    .split("/")
    .map((segment) => encodeURIComponent(segment))
    .join("/");
  return `/${encodedPath}`;
}

function normalizePath(basePath, targetPath) {
  if (
    /^https?:\/\//i.test(targetPath) ||
    targetPath.startsWith("mailto:") ||
    targetPath.startsWith("#")
  ) {
    return targetPath;
  }

  const baseSegments = basePath.split("/").slice(0, -1);
  const targetSegments = targetPath.startsWith("/")
    ? targetPath.slice(1).split("/")
    : [...baseSegments, ...targetPath.split("/")];
  const normalizedSegments = [];

  for (const segment of targetSegments) {
    if (!segment || segment === ".") {
      continue;
    }
    if (segment === "..") {
      normalizedSegments.pop();
      continue;
    }
    normalizedSegments.push(segment);
  }

  return normalizedSegments.join("/");
}

function navItemContainsPath(item, currentPath) {
  if (item.path === currentPath) {
    return true;
  }

  if (!Array.isArray(item.children)) {
    return false;
  }

  return item.children.some((child) => navItemContainsPath(child, currentPath));
}

function renderNavItems(items, currentPath, level = 0) {
  return items
    .map((item) => {
      const isActive = item.path === currentPath;
      const hasChildren = Array.isArray(item.children) && item.children.length > 0;
      const hasActiveDescendant = hasChildren
        ? item.children.some((child) => navItemContainsPath(child, currentPath))
        : false;
      const isExpanded = hasChildren && (isActive || hasActiveDescendant);

      const linkClasses = ["nav-link"];
      if (level > 0) {
        linkClasses.push("nav-link-child");
      }
      if (hasChildren) {
        linkClasses.push("nav-link-parent");
      }
      if (isActive) {
        linkClasses.push("active");
      } else if (hasActiveDescendant) {
        linkClasses.push("branch-active");
      }

      const childrenHtml =
        hasChildren
          ? `<ul class="nav-list nav-sublist${isExpanded ? " nav-sublist-expanded" : ""}">${renderNavItems(
              item.children,
              currentPath,
              level + 1
            )}</ul>`
          : "";

      return `
        <li class="nav-item nav-item-level-${level}">
          <a class="${linkClasses.join(" ")}" href="${buildHash(item.path)}">${escapeHtml(item.label)}</a>
          ${childrenHtml}
        </li>
      `;
    })
    .join("");
}

function renderNav(currentPath) {
  const sectionsHtml = NAV_SECTIONS.map((section) => {
    const itemsHtml = renderNavItems(section.items, currentPath);

    return `
      <section class="nav-section">
        <h3 class="nav-section-title">${escapeHtml(section.title)}</h3>
        <ul class="nav-list">${itemsHtml}</ul>
      </section>
    `;
  }).join("");

  navElement.innerHTML = sectionsHtml;
}

function renderLink(label, href, currentPath) {
  if (/^https?:\/\//i.test(href) || href.startsWith("mailto:")) {
    return `<a href="${escapeHtml(href)}" target="_blank" rel="noopener noreferrer">${escapeHtml(
      label
    )}</a>`;
  }

  if (href.startsWith("#")) {
    return `<a href="${escapeHtml(href)}">${escapeHtml(label)}</a>`;
  }

  const resolvedPath = normalizePath(currentPath, href);
  if (resolvedPath.endsWith(".md") || resolvedPath.endsWith(".txt")) {
    return `<a href="${buildHash(resolvedPath)}">${escapeHtml(label)}</a>`;
  }

  return `<a href="${buildFileUrl(resolvedPath)}" target="_blank" rel="noopener noreferrer">${escapeHtml(
    label
  )}</a>`;
}

function renderImage(alt, src, currentPath) {
  const resolvedPath = normalizePath(currentPath, src);
  return `<img src="${buildFileUrl(resolvedPath)}" alt="${escapeHtml(alt)}" />`;
}

function renderInline(text, currentPath) {
  let working = text;
  const tokens = [];

  const stash = (html) => {
    const token = `@@TOKEN_${tokens.length}@@`;
    tokens.push(html);
    return token;
  };

  working = working.replace(/`([^`]+)`/g, (_, code) => {
    return stash(`<code>${escapeHtml(code)}</code>`);
  });

  working = working.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, (_, alt, src) => {
    return stash(renderImage(alt, src, currentPath));
  });

  working = working.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_, label, href) => {
    return stash(renderLink(label, href, currentPath));
  });

  working = escapeHtml(working);
  working = working.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  working = working.replace(/\*([^*]+)\*/g, "<em>$1</em>");

  tokens.forEach((html, index) => {
    working = working.replace(`@@TOKEN_${index}@@`, html);
  });

  return working;
}

function renderMarkdown(markdown, currentPath) {
  const lines = markdown.replace(/\r\n/g, "\n").split("\n");
  let html = "";
  let inCodeBlock = false;
  let codeLanguage = "";
  let codeLines = [];
  let paragraphLines = [];
  let listType = null;
  let listItems = [];
  let quoteLines = [];

  const flushParagraph = () => {
    if (!paragraphLines.length) {
      return;
    }
    html += `<p>${renderInline(paragraphLines.join(" "), currentPath)}</p>`;
    paragraphLines = [];
  };

  const flushList = () => {
    if (!listItems.length || !listType) {
      return;
    }
    const itemsHtml = listItems
      .map((item) => `<li>${renderInline(item, currentPath)}</li>`)
      .join("");
    html += `<${listType}>${itemsHtml}</${listType}>`;
    listItems = [];
    listType = null;
  };

  const flushQuote = () => {
    if (!quoteLines.length) {
      return;
    }
    html += `<blockquote>${renderInline(quoteLines.join(" "), currentPath)}</blockquote>`;
    quoteLines = [];
  };

  const flushCodeBlock = () => {
    const languageClass = codeLanguage ? ` class="language-${escapeHtml(codeLanguage)}"` : "";
    html += `<pre><code${languageClass}>${escapeHtml(codeLines.join("\n"))}</code></pre>`;
    codeLines = [];
    codeLanguage = "";
  };

  const flushAll = () => {
    flushParagraph();
    flushList();
    flushQuote();
  };

  for (const line of lines) {
    if (inCodeBlock) {
      if (line.startsWith("```")) {
        inCodeBlock = false;
        flushCodeBlock();
      } else {
        codeLines.push(line);
      }
      continue;
    }

    if (line.startsWith("```")) {
      flushAll();
      inCodeBlock = true;
      codeLanguage = line.slice(3).trim();
      continue;
    }

    if (!line.trim()) {
      flushAll();
      continue;
    }

    const headingMatch = line.match(/^(#{1,6})\s+(.*)$/);
    if (headingMatch) {
      flushAll();
      const level = headingMatch[1].length;
      const text = headingMatch[2].trim();
      html += `<h${level} id="${slugify(text)}">${renderInline(text, currentPath)}</h${level}>`;
      continue;
    }

    if (/^(-{3,}|_{3,}|\*{3,})$/.test(line.trim())) {
      flushAll();
      html += "<hr />";
      continue;
    }

    const quoteMatch = line.match(/^>\s?(.*)$/);
    if (quoteMatch) {
      flushParagraph();
      flushList();
      quoteLines.push(quoteMatch[1]);
      continue;
    }

    if (quoteLines.length) {
      flushQuote();
    }

    const orderedListMatch = line.match(/^\d+\.\s+(.*)$/);
    const unorderedListMatch = line.match(/^[-*+]\s+(.*)$/);

    if (orderedListMatch || unorderedListMatch) {
      flushParagraph();
      const nextType = orderedListMatch ? "ol" : "ul";
      if (listType && listType !== nextType) {
        flushList();
      }
      listType = nextType;
      listItems.push((orderedListMatch || unorderedListMatch)[1]);
      continue;
    }

    if (listItems.length) {
      flushList();
    }

    paragraphLines.push(line.trim());
  }

  if (inCodeBlock) {
    flushCodeBlock();
  }

  flushAll();
  return html;
}

async function loadPage() {
  const path = parseRoute();
  renderNav(path);
  pagePathElement.textContent = path;
  pageTitleElement.textContent = "Loading...";
  pageContentElement.innerHTML = "<p>Loading wiki page...</p>";

  if (path.toLowerCase().endsWith(".pdf")) {
    const fileUrl = buildFileUrl(path);
    pageTitleElement.textContent = path.split("/").at(-1);
    pageContentElement.innerHTML = `
      <div class="error-card">
        <p><strong>PDF files are opened directly</strong> instead of being rendered in the wiki viewer.</p>
        <p><a href="${escapeHtml(fileUrl)}" target="_blank" rel="noopener noreferrer">Open PDF</a></p>
      </div>
    `;
    document.title = `${path.split("/").at(-1)} | Melee Modding Wiki`;
    return;
  }

  try {
    const response = await fetch(buildFileUrl(path), { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const source = await response.text();
    const titleMatch = source.match(/^#\s+(.+)$/m);
    const title = titleMatch ? titleMatch[1].trim() : path.split("/").at(-1);

    pageTitleElement.textContent = title;
    if (path.endsWith(".txt")) {
      pageContentElement.innerHTML = `<pre><code>${escapeHtml(source)}</code></pre>`;
    } else if (path.endsWith(".json")) {
      try {
        const parsed = JSON.parse(source);
        pageContentElement.innerHTML = `<pre><code class="language-json">${escapeHtml(
          JSON.stringify(parsed, null, 2)
        )}</code></pre>`;
      } catch {
        pageContentElement.innerHTML = `<pre><code class="language-json">${escapeHtml(source)}</code></pre>`;
      }
    } else {
      pageContentElement.innerHTML = renderMarkdown(source, path);
    }
    document.title = `${title} | Melee Modding Wiki`;
  } catch (error) {
    pageTitleElement.textContent = "Page Not Found";
    pageContentElement.innerHTML = `
      <div class="error-card">
        <p><strong>Could not load:</strong> <code>${escapeHtml(path)}</code></p>
        <p>Make sure you started the local wiki server from the repo root. The expected URL is <code>http://127.0.0.1:4173/wiki/</code>.</p>
        <p>Error: <code>${escapeHtml(String(error.message || error))}</code></p>
      </div>
    `;
    document.title = "Wiki Error | Melee Modding Wiki";
  }
}

window.addEventListener("hashchange", loadPage);
loadPage();
