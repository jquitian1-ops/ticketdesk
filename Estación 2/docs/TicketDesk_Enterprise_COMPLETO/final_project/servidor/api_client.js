/**
 * TicketDesk API Client v2.0
 * Maneja autenticación JWT, WebSocket, reintentos y paginación
 * Se incluye en los 3 portales HTML para conectarse al servidor
 */
const TicketDeskAPI = (() => {
  const CFG = {
    base: localStorage.getItem('tdv2_server') || 'http://localhost:5050',
    wsBase: (localStorage.getItem('tdv2_server') || 'http://localhost:5050')
             .replace(/^http/, 'ws'),
  };

  let _token   = localStorage.getItem('tdv2_jwt') || null;
  let _socket  = null;
  let _handlers = {};
  let _heartbeatTimer = null;
  let _reconnectTimer = null;
  let _pageCache = {};

  // ── Auth headers ──────────────────────────────────
  function headers() {
    const h = { 'Content-Type': 'application/json' };
    if (_token) h['Authorization'] = 'Bearer ' + _token;
    return h;
  }

  // ── Fetch with retry ──────────────────────────────
  async function apiFetch(path, opts = {}, retries = 2) {
    const url = CFG.base + path;
    const options = { headers: headers(), ...opts };
    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
        const res = await fetch(url, options);
        if (res.status === 401) { _token = null; localStorage.removeItem('tdv2_jwt'); }
        if (res.status === 409) {
          const data = await res.json();
          throw Object.assign(new Error('conflict'), { conflict: true, data });
        }
        return await res.json();
      } catch (e) {
        if (e.conflict) throw e;
        if (attempt === retries) throw e;
        await new Promise(r => setTimeout(r, 500 * (attempt + 1)));
      }
    }
  }

  // ── Login ─────────────────────────────────────────
  async function login(username, password, company_id, portal) {
    const data = await apiFetch('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password, company_id, portal })
    });
    if (data.success) {
      _token = data.token;
      localStorage.setItem('tdv2_jwt', _token);
      localStorage.setItem('tdv2_user', JSON.stringify(data.user));
      startHeartbeat(portal);
    }
    return data;
  }

  async function logout() {
    try { await apiFetch('/api/auth/logout', { method: 'POST' }); } catch(e) {}
    _token = null;
    localStorage.removeItem('tdv2_jwt');
    localStorage.removeItem('tdv2_user');
    stopHeartbeat();
    if (_socket) _socket.disconnect();
  }

  // ── Heartbeat ─────────────────────────────────────
  function startHeartbeat(portal) {
    stopHeartbeat();
    _heartbeatTimer = setInterval(async () => {
      try { await apiFetch('/api/auth/heartbeat', {
        method: 'POST', body: JSON.stringify({ portal }) }); }
      catch(e) {}
    }, 60000);
  }
  function stopHeartbeat() {
    if (_heartbeatTimer) clearInterval(_heartbeatTimer);
  }

  // ── Tickets (with pagination + cache) ─────────────
  async function getTickets(filters = {}) {
    const params = new URLSearchParams({ page:1, per_page:100, ...filters }).toString();
    return apiFetch(`/api/tickets?${params}`);
  }

  async function getAllTicketPages(filters = {}) {
    let page = 1, all = [];
    while (true) {
      const data = await getTickets({ ...filters, page, per_page: 200 });
      if (!data.success) break;
      all = all.concat(data.tickets || []);
      if (page >= (data.pages || 1)) break;
      page++;
    }
    return all;
  }

  async function getTicket(id)         { return apiFetch(`/api/tickets/${id}`); }
  async function createTicket(body)    { return apiFetch('/api/tickets', { method:'POST', body:JSON.stringify(body) }); }
  async function updateTicket(id,body) { return apiFetch(`/api/tickets/${id}`, { method:'PUT', body:JSON.stringify(body) }); }
  async function deleteTicket(id)      { return apiFetch(`/api/tickets/${id}`, { method:'DELETE' }); }
  async function addComment(id,text,isInternal=false) {
    return apiFetch(`/api/tickets/${id}/comments`, { method:'POST', body:JSON.stringify({ text, is_internal:isInternal }) });
  }
  async function addSurvey(id,rating,comment='') {
    return apiFetch(`/api/tickets/${id}/survey`, { method:'POST', body:JSON.stringify({ rating, comment }) });
  }
  async function logTime(id,seconds,note='') {
    return apiFetch(`/api/tickets/${id}/time`, { method:'POST', body:JSON.stringify({ seconds, note }) });
  }
  async function getStats(company_id) {
    const p = company_id ? `?company_id=${company_id}` : '';
    return apiFetch(`/api/stats${p}`);
  }

  // ── Sessions ──────────────────────────────────────
  async function getSessions()          { return apiFetch('/api/sessions'); }
  async function kickUser(username)     { return apiFetch(`/api/sessions/${username}/kick`, { method:'POST' }); }
  async function kickAll()              { return apiFetch('/api/sessions/kick-all', { method:'POST' }); }

  // ── Config / Team / FAQ ───────────────────────────
  async function getConfig()            { return apiFetch('/api/config'); }
  async function saveConfig(data)       { return apiFetch('/api/config', { method:'POST', body:JSON.stringify(data) }); }
  async function getTeam()              { return apiFetch('/api/team'); }
  async function addTeamMember(data)    { return apiFetch('/api/team', { method:'POST', body:JSON.stringify(data) }); }
  async function removeTeamMember(id)   { return apiFetch(`/api/team/${id}`, { method:'DELETE' }); }
  async function getBotFAQ(q='')        { return apiFetch(`/api/bot/faq${q?'?q='+encodeURIComponent(q):''}`);}
  async function getUsers()             { return apiFetch('/api/users'); }
  async function createUser(data)       { return apiFetch('/api/users', { method:'POST', body:JSON.stringify(data) }); }
  async function updateUser(u,data)     { return apiFetch(`/api/users/${u}`, { method:'PUT', body:JSON.stringify(data) }); }
  async function deleteUser(u)          { return apiFetch(`/api/users/${u}`, { method:'DELETE' }); }
  async function health()               { return apiFetch('/api/health'); }

  // ── WebSocket (real-time) ─────────────────────────
  function connectWS(user, onEvent) {
    if (typeof io === 'undefined') return;
    if (_socket) _socket.disconnect();

    _socket = io(CFG.base, {
      auth: { token: _token },
      reconnection: true,
      reconnectionDelay: 2000,
      reconnectionAttempts: 10,
      transports: ['websocket','polling']
    });

    _socket.on('connect', () => {
      _socket.emit('join', {
        company_id: user.company_id,
        username:   user.username,
        role:       user.role
      });
    });

    const events = ['ticket_created','ticket_updated','ticket_deleted',
                    'comment_added','user_connected','user_disconnected','kicked'];
    events.forEach(ev => {
      _socket.on(ev, data => {
        if (onEvent) onEvent(ev, data);
        const h = _handlers[ev];
        if (h) h(data);
      });
    });

    _socket.on('kicked', () => {
      alert('Tu sesión fue cerrada por el administrador.');
      logout();
      location.reload();
    });
  }

  function onEvent(event, handler) { _handlers[event] = handler; }

  // ── Server config ─────────────────────────────────
  function setServer(url) {
    localStorage.setItem('tdv2_server', url);
    CFG.base = url;
  }
  function getServer() { return CFG.base; }
  function isConnected() { return !!_token; }
  function currentUser() {
    try { return JSON.parse(localStorage.getItem('tdv2_user') || 'null'); } catch(e) { return null; }
  }

  return {
    login, logout, health, setServer, getServer, isConnected, currentUser,
    getTickets, getAllTicketPages, getTicket, createTicket, updateTicket,
    deleteTicket, addComment, addSurvey, logTime, getStats,
    getSessions, kickUser, kickAll,
    getConfig, saveConfig, getTeam, addTeamMember, removeTeamMember,
    getBotFAQ, getUsers, createUser, updateUser, deleteUser,
    connectWS, onEvent
  };
})();
