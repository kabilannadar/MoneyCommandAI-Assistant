(function () {
  // 0. Single-instance guard — if an iframe already exists, do nothing.
  //    This handles React StrictMode double-mount where cleanup runs
  //    BEFORE the second mount, clearing any window-level flags.
  if (document.querySelector('iframe[title="MoneyCommandAI Assistant"]')) return;

  // 1. Determine the chatbot host URL from this script's src attribute
  var scriptEl = document.currentScript || (function () {
    var scripts = document.getElementsByTagName('script');
    return scripts[scripts.length - 1];
  })();

  var chatbotUrl = "https://chatbotf-production.up.railway.app";
  if (scriptEl && scriptEl.src) {
    try {
      var urlObj = new URL(scriptEl.src);
      chatbotUrl = urlObj.origin;
    } catch (e) { }
  }

  // 2. Track whether we're currently in mobile mode (≤480px parent page)
  var isMobile = window.innerWidth <= 480;

  // 3. Create the iframe
  var iframe = document.createElement('iframe');
  iframe.src = chatbotUrl + '?mobile=' + isMobile;
  iframe.style.position = 'fixed';
  iframe.style.bottom = '0px';
  iframe.style.right = '0px';
  iframe.style.left = 'auto';
  iframe.style.top = 'auto';
  iframe.style.border = 'none';
  iframe.style.zIndex = '999999';
  iframe.style.background = 'transparent';
  iframe.style.filter = 'drop-shadow(0 12px 30px rgba(0, 0, 0, 0.28)) drop-shadow(0 4px 10px rgba(0, 0, 0, 0.16))';
  iframe.style.transition = 'none'; // no geometry transitions — ever
  iframe.title = 'MoneyCommandAI Assistant';
  iframe.setAttribute('allow', 'autoplay');

  // Set permanent size based on viewport — recalculated on resize
  function setPermanentSize() {
    var width = window.innerWidth;
    var height = window.innerHeight;
    if (width <= 480) {
      // Mobile: fullscreen always
      iframe.style.width = '100%';
      iframe.style.height = '100%';
      iframe.style.left = '0px';
      iframe.style.top = '0px';
      iframe.style.right = 'auto';
      iframe.style.bottom = 'auto';
    } else if (width <= 768) {
      // Tablet: medium window overlay — cap height to viewport
      var tabletH = Math.min(820, height - 20);
      iframe.style.width = '480px';
      iframe.style.height = tabletH + 'px';
      iframe.style.left = 'auto';
      iframe.style.top = 'auto';
      iframe.style.right = '0px';
      iframe.style.bottom = '0px';
    } else if (width <= 1024) {
      // Small desktop: slightly compact window
      var smDesktopH = Math.min(820, height - 20);
      iframe.style.width = '460px';
      iframe.style.height = smDesktopH + 'px';
      iframe.style.left = 'auto';
      iframe.style.top = 'auto';
      iframe.style.right = '0px';
      iframe.style.bottom = '0px';
    } else {
      // Large desktop: full window overlay
      var desktopH = Math.min(820, height - 20);
      iframe.style.width = '520px';
      iframe.style.height = desktopH + 'px';
      iframe.style.left = 'auto';
      iframe.style.top = 'auto';
      iframe.style.right = '0px';
      iframe.style.bottom = '0px';
    }
  }

  // Post current mobile state into the iframe
  function postResizeMessage() {
    try {
      if (iframe.contentWindow) {
        iframe.contentWindow.postMessage({
          type: 'moneycommandai-parent-resize',
          isMobile: window.innerWidth <= 480
        }, chatbotUrl);
      }
    } catch (e) { }
  }

  // Debounce helper — prevents excessive resize recalculations
  function debounce(fn, delay) {
    var timer;
    return function () {
      clearTimeout(timer);
      timer = setTimeout(fn, delay);
    };
  }

  // Append to document body
  if (document.body) {
    document.body.appendChild(iframe);
  } else {
    window.addEventListener('DOMContentLoaded', function () {
      document.body.appendChild(iframe);
    });
  }

  // Initialize size
  setPermanentSize();

  // 4. Pointer-events tracking
  //    When chat is closed, we set pointer-events: none on the iframe so the empty space
  //    doesn't block clicks on the parent page. But if the mouse/touch moves over the FAB
  //    region, we enable pointer-events so they are clickable.
  //    When chat is open, pointer-events is always auto.
  var isOpen = false;

  // Track last known cursor position so we can evaluate pointer-events immediately
  // when the chat closes, without waiting for the next mousemove event.
  var lastCursorX = -999;
  var lastCursorY = -999;

  function isOverFabRegion(clientX, clientY) {
    var width = window.innerWidth;
    var height = window.innerHeight;
    if (width <= 480) {
      // Mobile: small bottom-right tap zone
      return (clientX > width - 100) && (clientY > height - 100);
    }
    // Desktop/Tablet: covers FAB (74x74 at bottom:50, right:50) plus tooltip above it
    return (clientX > width - 300) && (clientY > height - 180);
  }

  function updatePointerEvents(clientX, clientY) {
    if (isOpen) {
      iframe.style.pointerEvents = 'auto';
      return;
    }
    iframe.style.pointerEvents = isOverFabRegion(clientX, clientY) ? 'auto' : 'none';
  }

  // Mouse move listener on parent page — keeps lastCursorX/Y up to date
  window.addEventListener('mousemove', function (e) {
    lastCursorX = e.clientX;
    lastCursorY = e.clientY;
    updatePointerEvents(e.clientX, e.clientY);
  });

  // KEY FIX: mousedown/pointerdown on the parent fires even when the iframe has
  // pointer-events:none (because the event goes to the host page). We re-enable
  // pointer-events immediately so the subsequent 'click' event can reach the iframe.
  function handleParentClick(e) {
    lastCursorX = e.clientX;
    lastCursorY = e.clientY;
    if (!isOpen && isOverFabRegion(e.clientX, e.clientY)) {
      iframe.style.pointerEvents = 'auto';
    }
  }

  // Touch support — mirrors pointer/mouse handlers for iOS Safari compatibility
  function handleParentTouch(e) {
    if (e.touches && e.touches.length > 0) {
      var touch = e.touches[0];
      lastCursorX = touch.clientX;
      lastCursorY = touch.clientY;
      if (!isOpen && isOverFabRegion(touch.clientX, touch.clientY)) {
        iframe.style.pointerEvents = 'auto';
      }
    }
  }

  window.addEventListener('pointerdown', handleParentClick, true); // capture phase
  window.addEventListener('mousedown', handleParentClick, true);   // capture phase fallback
  window.addEventListener('touchstart', handleParentTouch, true);  // iOS Safari touch support

  // On parent window resize, recalculate size and sync isMobile state into iframe
  var handleResize = debounce(function () {
    var newIsMobile = window.innerWidth <= 480;
    setPermanentSize();
    // Only postMessage if isMobile changed, to avoid unnecessary re-renders
    if (newIsMobile !== isMobile) {
      isMobile = newIsMobile;
    }
    // Always post resize message so the iframe can sync layout state
    postResizeMessage();
  }, 150);

  window.addEventListener('resize', handleResize);

  // Send parent size immediately on iframe load to sync cross-origin state
  iframe.addEventListener('load', function () {
    postResizeMessage();
  });

  // 5. Listen for toggle and log messages from inside the iframe
  window.addEventListener('message', function (event) {
    if (event.origin !== chatbotUrl) return;

    var data = event.data;
    if (!data) return;

    if (data.type === 'moneycommandai-chatbot-toggle') {
      isOpen = !!data.open;
      if (isOpen) {
        iframe.style.pointerEvents = 'auto';
      } else {
        // When closing: if the cursor is already over the FAB zone (e.g. user's
        // mouse is still at the bottom-right corner after clicking Close), keep
        // pointer-events auto so the very next click on the FAB is not eaten.
        // Otherwise disable pointer-events so the closed iframe doesn't block
        // the host page content.
        iframe.style.pointerEvents = isOverFabRegion(lastCursorX, lastCursorY) ? 'auto' : 'none';
      }
    } else if (data.type === 'moneycommandai-log-transaction') {
      var text = data.text;
      var token = localStorage.getItem('token');
      var apiBase = window.location.origin;

      fetch(apiBase + '/api/telegram/log-text', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token ? 'Bearer ' + token : ''
        },
        body: JSON.stringify({ text: text })
      })
      .then(function (res) {
        if (!res.ok) {
          if (res.status === 401) {
            throw new Error('Authentication required. Please make sure you are logged in.');
          }
          return res.json().then(function (err) {
            throw new Error(err.detail || 'HTTP Error ' + res.status);
          }).catch(function () {
            throw new Error('HTTP Error ' + res.status);
          });
        }
        return res.json();
      })
      .then(function (json) {
        // Send response back to the iframe
        iframe.contentWindow.postMessage({
          type: 'moneycommandai-log-transaction-response',
          response: json
        }, chatbotUrl);

        // If logged successfully, dispatch custom event in parent to trigger React Query invalidation
        if (json.status === 'success') {
          window.dispatchEvent(new CustomEvent('moneycommandai-transaction-logged', { detail: json }));
        }
      })
      .catch(function (err) {
        console.error('[widget.js] Logging failed:', err);
        iframe.contentWindow.postMessage({
          type: 'moneycommandai-log-transaction-response',
          response: { status: 'error', message: err.message || 'Connection failed.' }
        }, chatbotUrl);
      });
    }
  });
})();
