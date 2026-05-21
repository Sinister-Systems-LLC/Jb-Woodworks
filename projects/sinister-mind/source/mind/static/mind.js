// Sinister Mind :: mind.js (v2 - tag chips + SSE live reload)
// Author: RKOJ-ELENO :: 2026-05-21
// License: AGPL-3.0-or-later

(async () => {
  const svg = d3.select("#graph");
  const tooltip = d3.select("#tooltip");

  function size() {
    const m = document.querySelector("main").getBoundingClientRect();
    return { w: m.width, h: m.height };
  }

  let currentGraph = null;
  let activeTags = new Set();

  async function loadGraph() {
    const resp = await fetch("/api/graph");
    return await resp.json();
  }

  async function render() {
    const graph = await loadGraph();
    currentGraph = graph;
    drawGraph(graph);
    renderSidebar(graph);
  }

  function renderSidebar(graph) {
    const stats = graph.counts || {};
    document.getElementById("stats").innerHTML = `
      <b>${stats.total_nodes}</b> nodes &middot; <b>${stats.total_edges}</b> edges<br>
      projects <b>${stats.projects}</b> &middot; brain <b>${stats.brain}</b><br>
      plans <b>${stats.plans}</b> &middot; PROGRESS <b>${stats.progress}</b><br>
      cross-agent <b>${stats.cross_agent}</b> &middot; resume-pts <b>${stats.resume_pts}</b>
    `;
    document.getElementById("title-status").textContent = "brain loaded";
    document.getElementById("title-counts").textContent = `${stats.total_nodes} nodes / ${stats.total_edges} edges`;

    // Project filter + pills
    const projects = graph.nodes.filter(n => n.type === "project");
    const projSelect = document.getElementById("project-filter");
    const pills = document.getElementById("project-pills");
    projSelect.innerHTML = '<option value="">— all projects —</option>';
    pills.innerHTML = "";
    projects.forEach(p => {
      const opt = document.createElement("option");
      opt.value = p.tags[0] || "";
      opt.textContent = p.label;
      projSelect.appendChild(opt);

      const pill = document.createElement("a");
      pill.className = "project-pill";
      pill.textContent = p.label;
      pill.title = p.tag || "";
      pill.dataset.key = p.tags[0] || "";
      pill.addEventListener("click", () => {
        document.querySelectorAll(".project-pill").forEach(el => el.classList.remove("active"));
        pill.classList.add("active");
        projSelect.value = pill.dataset.key;
        applyProjectFilter(pill.dataset.key);
      });
      pills.appendChild(pill);
    });

    // Tag cloud (PH4)
    const tagCounts = {};
    graph.nodes.forEach(n => {
      (n.tags || []).forEach(t => { tagCounts[t] = (tagCounts[t] || 0) + 1; });
    });
    const sortedTags = Object.entries(tagCounts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 40);
    const tagCloud = document.getElementById("tag-cloud");
    tagCloud.innerHTML = "";
    sortedTags.forEach(([tag, count]) => {
      const chip = document.createElement("span");
      chip.className = "tag-chip";
      chip.textContent = `${tag} (${count})`;
      chip.title = `${count} nodes tagged "${tag}"`;
      if (activeTags.has(tag)) chip.classList.add("active");
      chip.addEventListener("click", () => {
        if (activeTags.has(tag)) activeTags.delete(tag);
        else activeTags.add(tag);
        applyTagFilter();
        renderSidebar(currentGraph);
      });
      tagCloud.appendChild(chip);
    });
  }

  let linkSel, nodeSel, sim;
  function drawGraph(graph) {
    svg.selectAll("*").remove();
    const { w, h } = size();
    svg.attr("viewBox", `0 0 ${w} ${h}`);

    const linkGroup = svg.append("g").attr("class", "links");
    const nodeGroup = svg.append("g").attr("class", "nodes");

    linkSel = linkGroup.selectAll("line").data(graph.edges).enter().append("line").attr("class", "link");

    nodeSel = nodeGroup.selectAll("g").data(graph.nodes).enter().append("g")
      .attr("class", "node").attr("data-id", d => d.id);

    function radius(d) {
      if (d.type === "project") return 18;
      if (d.type === "brain") return 7;
      if (d.type === "plan") return 6;
      if (d.type === "resume_pt") return 8;
      return 4;
    }

    nodeSel.append("circle").attr("r", radius).attr("fill", d => d.color || "#A06EFF").style("color", d => d.color || "#A06EFF");
    nodeSel.filter(d => d.type === "project").append("text").attr("dy", 34).text(d => d.label);

    nodeSel.on("mouseenter", (event, d) => {
      const html = `
        <div class="ttl">${d.label}</div>
        <div>${d.type}${d.title ? " :: " + d.title : ""}</div>
        ${d.tag ? `<div class="tag">${d.tag}</div>` : ""}
        ${d.tags && d.tags.length ? `<div class="tag">${d.tags.slice(0, 6).join(", ")}</div>` : ""}
        <div style="color:var(--dim);font-size:9px;margin-top:6px;">${d.id}</div>
      `;
      tooltip.html(html).style("display", "block")
        .style("left", (event.pageX + 14) + "px")
        .style("top", (event.pageY + 14) + "px");
    })
    .on("mousemove", (event) => {
      tooltip.style("left", (event.pageX + 14) + "px").style("top", (event.pageY + 14) + "px");
    })
    .on("mouseleave", () => tooltip.style("display", "none"));

    sim = d3.forceSimulation(graph.nodes)
      .force("link", d3.forceLink(graph.edges).id(d => d.id).distance(70).strength(0.4))
      .force("charge", d3.forceManyBody().strength(-200))
      .force("center", d3.forceCenter(w / 2, h / 2))
      .force("collide", d3.forceCollide(d => radius(d) + 4))
      .on("tick", () => {
        linkSel
          .attr("x1", d => d.source.x).attr("y1", d => d.source.y)
          .attr("x2", d => d.target.x).attr("y2", d => d.target.y);
        nodeSel.attr("transform", d => `translate(${d.x},${d.y})`);
      });

    nodeSel.call(d3.drag()
      .on("start", (event, d) => { if (!event.active) sim.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
      .on("drag", (event, d) => { d.fx = event.x; d.fy = event.y; })
      .on("end", (event, d) => { if (!event.active) sim.alphaTarget(0); d.fx = null; d.fy = null; }));

    svg.call(d3.zoom().scaleExtent([0.2, 5]).on("zoom", (event) => {
      linkGroup.attr("transform", event.transform);
      nodeGroup.attr("transform", event.transform);
    }));
  }

  function applyProjectFilter(key) {
    if (!nodeSel) return;
    if (!key) {
      nodeSel.classed("dimmed", false);
      linkSel.classed("dimmed", false);
      return;
    }
    nodeSel.classed("dimmed", d => {
      if (d.type === "project") return d.tags[0] !== key;
      if (d.tags && d.tags.length) return !d.tags.some(t => t === key || t.startsWith(key));
      return true;
    });
    linkSel.classed("dimmed", d => {
      const src = typeof d.source === "object" ? d.source : currentGraph.nodes.find(n => n.id === d.source);
      const tgt = typeof d.target === "object" ? d.target : currentGraph.nodes.find(n => n.id === d.target);
      const srcMatches = src && ((src.type === "project" && src.tags[0] === key) || (src.tags && src.tags.some(t => t === key || t.startsWith(key))));
      const tgtMatches = tgt && ((tgt.type === "project" && tgt.tags[0] === key) || (tgt.tags && tgt.tags.some(t => t === key || t.startsWith(key))));
      return !(srcMatches && tgtMatches);
    });
  }

  function applyTagFilter() {
    if (!nodeSel) return;
    if (activeTags.size === 0) {
      nodeSel.classed("dimmed", false);
      linkSel.classed("dimmed", false);
      return;
    }
    nodeSel.classed("dimmed", d => {
      if (!d.tags || !d.tags.length) return true;
      return !d.tags.some(t => activeTags.has(t));
    });
    linkSel.classed("dimmed", d => {
      const src = typeof d.source === "object" ? d.source : currentGraph.nodes.find(n => n.id === d.source);
      const tgt = typeof d.target === "object" ? d.target : currentGraph.nodes.find(n => n.id === d.target);
      const srcM = src && src.tags && src.tags.some(t => activeTags.has(t));
      const tgtM = tgt && tgt.tags && tgt.tags.some(t => activeTags.has(t));
      return !(srcM && tgtM);
    });
  }

  // Wire interactions
  document.getElementById("project-filter").addEventListener("change", (e) => applyProjectFilter(e.target.value));

  const searchInput = document.getElementById("search-input");
  const searchResults = document.getElementById("search-results");
  let searchTimer = null;
  searchInput.addEventListener("input", () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(async () => {
      const q = searchInput.value.trim();
      if (!q) { searchResults.innerHTML = ""; return; }
      const r = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
      const data = await r.json();
      searchResults.innerHTML = "";
      (data.matches || []).slice(0, 20).forEach(m => {
        const hit = document.createElement("a");
        hit.className = "search-hit";
        hit.textContent = `${m.type[0]} :: ${m.label}`;
        hit.title = m.id;
        hit.addEventListener("click", () => {
          const sel = svg.select(`g[data-id="${m.id}"]`);
          if (!sel.empty()) {
            const { w, h } = size();
            const node = sel.datum();
            const transform = d3.zoomIdentity.translate(w / 2 - node.x, h / 2 - node.y).scale(1.5);
            svg.transition().duration(500).call(d3.zoom().transform, transform);
            sel.select("circle").attr("stroke", "#FFD66E").attr("stroke-width", 4);
            setTimeout(() => sel.select("circle").attr("stroke", "rgba(255,255,255,0.08)").attr("stroke-width", 1.5), 2000);
          }
        });
        searchResults.appendChild(hit);
      });
    }, 200);
  });

  document.getElementById("path-go").addEventListener("click", async () => {
    const a = document.getElementById("path-a").value.trim();
    const b = document.getElementById("path-b").value.trim();
    const pathResult = document.getElementById("path-result");
    if (!a || !b) { pathResult.textContent = "need both A and B"; return; }
    const r = await fetch(`/api/path?a=${encodeURIComponent(a)}&b=${encodeURIComponent(b)}`);
    const data = await r.json();
    if (!data.found) { pathResult.textContent = "no path"; linkSel.classed("highlighted", false); return; }
    pathResult.textContent = `${data.length} hops`;
    const pathSet = new Set();
    for (let i = 0; i < data.path.length - 1; i++) {
      pathSet.add(`${data.path[i]}|${data.path[i + 1]}`);
      pathSet.add(`${data.path[i + 1]}|${data.path[i]}`);
    }
    linkSel.classed("highlighted", d => {
      const s = typeof d.source === "object" ? d.source.id : d.source;
      const t = typeof d.target === "object" ? d.target.id : d.target;
      return pathSet.has(`${s}|${t}`);
    });
  });

  // PH7: SSE live reload
  function startSSE() {
    if (!window.EventSource) return;
    try {
      const es = new EventSource("/api/stream");
      es.addEventListener("graph-change", () => {
        document.getElementById("live-status").textContent = "reloading";
        setTimeout(async () => {
          await render();
          document.getElementById("live-status").textContent = "live";
        }, 100);
      });
      es.addEventListener("error", () => {
        document.getElementById("live-status").textContent = "offline";
        setTimeout(startSSE, 5000);
      });
    } catch (e) {
      document.getElementById("live-status").textContent = "offline";
    }
  }

  await render();
  startSSE();
})();
