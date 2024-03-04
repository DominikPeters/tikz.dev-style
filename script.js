let sections;
let navLi;

function debounce(func, timeout = 300) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => {
      func.apply(this, args);
    }, timeout);
  };
}

function updateTOC() {
  var current = "NOTHING";

  sections.forEach((section) => {
    const sectionTop = section.offsetTop;
    if (scrollY >= sectionTop - 122) {
      current = section.getAttribute("id");
    }
  });

  navLi.forEach((li) => {
    li.parentElement.classList.remove("current");
    if (li.href.endsWith(current)) {
      li.parentElement.classList.add("current");
      li.parentElement.scrollIntoView({ block: "nearest" });
    }
  });
}

function makeAnchorButtons() {
  document.querySelectorAll('a.anchor-link').forEach((element) => {
    const links = [];
    if (element.dataset.htmlLink) {
      // Create the HTML link element
      const htmlLink = document.createElement('a');
      htmlLink.href = `#${element.dataset.htmlLink}`;
      htmlLink.className = 'anchor-html-link';
      htmlLink.setAttribute('aria-label', 'Permalink to this section in HTML version');
      htmlLink.title = 'Share link';
      htmlLink.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" class="bi bi-link" viewBox="0 0 16 16"><path d="M 10.5,15 C 10.223858,15 10,14.776142 10,14.5 V 2 H 9 v 12.5 c 0,0.666666 -1,0.666666 -1,0 L 7.9351199,7.077646 H 7.0029165 C 2.9055303,7.077646 2.7647133,1 7,1 h 5.5 c 0.666666,0 0.666666,1 0,1 H 11 v 12.5 c 0,0.276142 -0.223858,0.5 -0.5,0.5 z"/></svg>';
      if (!element.dataset.pdfDestination) {
        htmlLink.style.marginLeft = 'auto';
      }
      links.push(htmlLink);
    }

    element.replaceWith(...links);
  });
}

document.addEventListener("DOMContentLoaded", (event) => {
  sections = document.querySelectorAll("span.sectionnumber");
  navLi = document.querySelectorAll("#local-toc-container a");

  window.onscroll = () => {
    debounce(updateTOC, 75)();
    const pgfplots = document.getElementById("pgfplots-link");
    if (pgfplots) {
      pgfplots.style.display = scrollY == 0 ? "block" : "none";
    }
  };

  const hamburger = document.getElementById("hamburger-button");
  const chapterMenu = document.getElementById("chapter-toc-container");
  function toggleMenu() {
    if (chapterMenu.classList.contains("show-menu")) {
      chapterMenu.classList.remove("show-menu");
    } else {
      chapterMenu.classList.add("show-menu");
    }
  }
  hamburger.addEventListener("click", toggleMenu);


  makeAnchorButtons();

  /*! instant.page v5.1.0 - (C) 2019-2020 Alexandre Dieulot - https://instant.page/license */
  let t,e;const n=new Set,o=document.createElement("link"),i=o.relList&&o.relList.supports&&o.relList.supports("prefetch")&&window.IntersectionObserver&&"isIntersecting"in IntersectionObserverEntry.prototype,s="instantAllowQueryString"in document.body.dataset,a="instantAllowExternalLinks"in document.body.dataset,r="instantWhitelist"in document.body.dataset,c="instantMousedownShortcut"in document.body.dataset,d=1111;let l=65,u=!1,f=!1,m=!1;if("instantIntensity"in document.body.dataset){const t=document.body.dataset.instantIntensity;if("mousedown"==t.substr(0,"mousedown".length))u=!0,"mousedown-only"==t&&(f=!0);else if("viewport"==t.substr(0,"viewport".length))navigator.connection&&(navigator.connection.saveData||navigator.connection.effectiveType&&navigator.connection.effectiveType.includes("2g"))||("viewport"==t?document.documentElement.clientWidth*document.documentElement.clientHeight<45e4&&(m=!0):"viewport-all"==t&&(m=!0));else{const e=parseInt(t);isNaN(e)||(l=e)}}if(i){const n={capture:!0,passive:!0};if(f||document.addEventListener("touchstart",function(t){e=performance.now();const n=t.target.closest("a");if(!h(n))return;v(n.href)},n),u?c||document.addEventListener("mousedown",function(t){const e=t.target.closest("a");if(!h(e))return;v(e.href)},n):document.addEventListener("mouseover",function(n){if(performance.now()-e<d)return;const o=n.target.closest("a");if(!h(o))return;o.addEventListener("mouseout",p,{passive:!0}),t=setTimeout(()=>{v(o.href),t=void 0},l)},n),c&&document.addEventListener("mousedown",function(t){if(performance.now()-e<d)return;const n=t.target.closest("a");if(t.which>1||t.metaKey||t.ctrlKey)return;if(!n)return;n.addEventListener("click",function(t){1337!=t.detail&&t.preventDefault()},{capture:!0,passive:!1,once:!0});const o=new MouseEvent("click",{view:window,bubbles:!0,cancelable:!1,detail:1337});n.dispatchEvent(o)},n),m){let t;(t=window.requestIdleCallback?t=>{requestIdleCallback(t,{timeout:1500})}:t=>{t()})(()=>{const t=new IntersectionObserver(e=>{e.forEach(e=>{if(e.isIntersecting){const n=e.target;t.unobserve(n),v(n.href)}})});document.querySelectorAll("a").forEach(e=>{h(e)&&t.observe(e)})})}}function p(e){e.relatedTarget&&e.target.closest("a")==e.relatedTarget.closest("a")||t&&(clearTimeout(t),t=void 0)}function h(t){if(t&&t.href&&(!r||"instant"in t.dataset)&&(a||t.origin==location.origin||"instant"in t.dataset)&&["http:","https:"].includes(t.protocol)&&("http:"!=t.protocol||"https:"!=location.protocol)&&(s||!t.search||"instant"in t.dataset)&&!(t.hash&&t.pathname+t.search==location.pathname+location.search||"noInstant"in t.dataset))return!0}function v(t){if(n.has(t))return;const e=document.createElement("link");e.rel="prefetch",e.href=t,document.head.appendChild(e),n.add(t)}
});

window.addEventListener("load", () => {
  document
    .querySelector("#chapter-toc-container p.current")
    .scrollIntoView({ block: "nearest" });
  updateTOC();
});
