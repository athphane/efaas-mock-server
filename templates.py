LOGIN_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>eFaas Mock — Login</title>
<style>
  :root { --navy: #1a237e; --border: #dfe3ea; --muted: #6b7280; --panel: rgba(255,255,255,.96); }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html, body { height: 100%; }
  body { font-family: -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; background: radial-gradient(circle at top left,#e8eaff 0,#f4f6fb 34%,#edf1f7 100%); color: #1f2937; min-height: 100vh; overflow: hidden; }
  .banner { min-height: 48px; background: linear-gradient(135deg,#1a237e,#283593); color: #fff; padding: 10px 24px; display: flex; align-items: center; justify-content: center; gap: 8px; text-align: center; font-size: 13px; }
  .banner strong { font-size: 16px; }
  .banner a { color: #fff; text-decoration: underline; margin-left: 8px; }
  .container { max-width: 1360px; height: calc(100vh - 48px); margin: 0 auto; padding: 14px 18px 18px; display: flex; flex-direction: column; min-height: 0; }
  .tabs { flex: 0 0 auto; display: flex; gap: 8px; margin-bottom: 12px; }
  .tab { padding: 10px 14px; text-align: center; background: #e5e7eb; border: 1px solid #d7dce5; border-radius: 999px; cursor: pointer; font-weight: 700; font-size: 13px; transition: all .15s; user-select: none; }
  .tab.active { background: #fff; color: var(--navy); border-color: #fff; box-shadow: 0 8px 22px rgba(31,41,55,.10); }
  .tab:hover:not(.active) { background: #dfe3ea; }
  .panel { display: none; flex: 1; min-height: 0; }
  .panel.active { display: block; }
  .auth-layout { display: grid; grid-template-columns: minmax(480px,1.45fr) minmax(380px,.95fr); gap: 14px; height: 100%; min-height: 0; }
  .panel-card { background: var(--panel); border: 1px solid var(--border); border-radius: 16px; box-shadow: 0 16px 40px rgba(31,41,55,.10); min-width: 0; min-height: 0; }
  .account-panel, .settings-panel { display: flex; flex-direction: column; padding: 14px; }
  .panel-header { flex: 0 0 auto; display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 10px; }
  .panel-title { font-size: 16px; font-weight: 800; color: #111827; }
  .panel-kicker { font-size: 12px; color: var(--muted); margin-top: 2px; }
  .count-pill { flex: 0 0 auto; border-radius: 999px; background: #eef2ff; color: var(--navy); padding: 5px 9px; font-size: 12px; font-weight: 800; }
  .search-box { flex: 0 0 auto; width: 100%; padding: 9px 12px; border: 1px solid var(--border); border-radius: 10px; font-size: 13px; outline: none; transition: border-color .2s, box-shadow .2s; }
  .search-box:focus { border-color: var(--navy); box-shadow: 0 0 0 3px rgba(26,35,126,.10); }
  .results-row { flex: 0 0 auto; display: flex; align-items: center; justify-content: space-between; gap: 10px; margin: 8px 0; }
  .results-info, .pick-hint { font-size: 12px; color: var(--muted); }
  .pick-hint { text-align: right; }
  .user-grid { flex: 1; min-height: 0; display: grid; grid-template-columns: repeat(auto-fill,minmax(235px,1fr)); align-content: start; gap: 8px; overflow-y: auto; padding-right: 4px; }
  .user-card { min-width: 0; border: 1px solid #e4e7ee; border-radius: 10px; padding: 9px 10px; cursor: pointer; background: #fff; transition: all .15s; }
  .user-card:hover { border-color: var(--navy); background: #f7f8ff; box-shadow: 0 4px 12px rgba(26,35,126,.08); }
  .user-card.selected { border-color: var(--navy); background: #e8eaff; box-shadow: inset 3px 0 0 var(--navy); }
  .user-card .name { font-weight: 700; font-size: 13px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .user-card .meta { font-size: 11px; color: var(--muted); margin-top: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .user-card .type { display: inline-block; font-size: 10px; font-weight: 700; padding: 2px 7px; border-radius: 999px; margin-top: 5px; }
  .type-maldivian { background: #e8f5e9; color: #2e7d32; }
  .type-workpermit { background: #fff3e0; color: #e65100; }
  .type-foreigner { background: #e3f2fd; color: #1565c0; }
  .no-results { text-align: center; padding: 18px; color: #999; font-size: 13px; border: 1px dashed var(--border); border-radius: 10px; margin-top: 8px; }
  .selected-info { flex: 0 0 auto; background: #e8eaff; border: 1px solid #cdd4ff; border-left: 4px solid var(--navy); border-radius: 10px; padding: 9px 11px; margin-bottom: 10px; font-size: 12px; display: none; }
  .selected-info.show { display: block; }
  .settings-body, .create-fields { flex: 1; min-height: 0; overflow: auto; padding-right: 4px; }
  .scope-box, .logout-box { margin: 0 0 10px; padding: 12px; border: 1px solid var(--border); border-radius: 12px; }
  .scope-box { background: #fafbff; }
  .logout-box { background: #fffdf7; }
  .scope-title { font-size: 13px; font-weight: 800; color: var(--navy); margin-bottom: 4px; }
  .scope-note { font-size: 11px; color: var(--muted); line-height: 1.35; margin-bottom: 10px; }
  .scope-grid { display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: 8px; }
  .scope-option { display: flex; gap: 8px; align-items: flex-start; min-width: 0; padding: 8px 9px; border: 1px solid #dfe3ea; border-radius: 9px; background: #fff; cursor: pointer; }
  .scope-option input { width: auto; flex: 0 0 auto; margin-top: 2px; }
  .scope-option span { min-width: 0; }
  .scope-option strong { display: block; font-size: 12px; line-height: 1.2; color: #333; }
  .scope-option small { display: block; font-size: 11px; line-height: 1.25; color: var(--muted); margin-top: 2px; }
  .scope-option.required { background: #f3f5ff; border-color: #cdd4ff; }
  .scope-option.required input { cursor: not-allowed; }
  .logout-grid, .form-grid { display: grid; gap: 9px 10px; }
  .form-grid { grid-template-columns: 1fr 1fr; }
  .logout-grid .full, .form-grid .full { grid-column: 1 / -1; }
  label:not(.scope-option) { display: block; font-size: 12px; font-weight: 700; color: #4b5563; margin-bottom: 4px; }
  input, select { width: 100%; padding: 8px 10px; border: 1px solid var(--border); border-radius: 8px; font-size: 13px; outline: none; transition: border-color .2s, box-shadow .2s; }
  input:focus, select:focus { border-color: var(--navy); box-shadow: 0 0 0 3px rgba(26,35,126,.10); }
  .btn { display: inline-flex; align-items: center; justify-content: center; padding: 11px 18px; font-size: 14px; font-weight: 800; border: none; border-radius: 10px; cursor: pointer; transition: all .15s; }
  .btn-primary { background: var(--navy); color: #fff; width: 100%; }
  .btn-primary:hover:not(:disabled) { background: #283593; transform: translateY(-1px); box-shadow: 0 8px 18px rgba(26,35,126,.25); }
  .btn-primary:disabled { opacity: .45; cursor: not-allowed; }
  .actions { flex: 0 0 auto; display: flex; gap: 10px; margin-top: 10px; padding-top: 10px; border-top: 1px solid #eef0f5; }
  .actions .btn { flex: 1; }
  .create-intro { font-size: 12px; color: var(--muted); line-height: 1.4; margin-bottom: 10px; }
  @media (max-height: 720px) and (min-width: 901px) {
    .banner { min-height: 42px; padding: 8px 18px; }
    .container { height: calc(100vh - 42px); padding: 10px 14px 14px; }
    .tabs { margin-bottom: 8px; }
    .panel-header { margin-bottom: 8px; }
    .scope-note { display: none; }
    .scope-option { padding: 7px 8px; }
    .user-card { padding: 8px 9px; }
  }
  @media (max-width: 900px) {
    html, body { height: auto; }
    body { overflow: auto; }
    .banner { flex-wrap: wrap; }
    .container { height: auto; min-height: calc(100vh - 48px); padding: 12px; }
    .tabs { overflow-x: auto; }
    .panel.active { display: block; }
    .auth-layout { display: block; height: auto; }
    .panel-card { margin-bottom: 12px; }
    .user-grid { max-height: 55vh; }
    .settings-body, .create-fields { overflow: visible; }
    .scope-grid, .form-grid { grid-template-columns: 1fr; }
  }
</style>
</head>
<body>
<div class="banner">
  <strong>eFaas Mock Server</strong> — Development only. No real authentication.
  <a href="/logout">Logout tester</a>
</div>
<div class="container">

  <div class="tabs">
    <div class="tab active" onclick="switchTab('select')">Select Existing User <small>({{ total_users }})</small></div>
    <div class="tab" onclick="switchTab('create')">Create New User</div>
  </div>

  <div id="panel-select" class="panel active">
    <div class="auth-layout">
      <section class="panel-card account-panel">
        <div class="panel-header">
          <div>
            <div class="panel-title">Select Existing User</div>
            <div class="panel-kicker">Search and choose a seeded mock account.</div>
          </div>
          <div class="count-pill">{{ total_users }} users</div>
        </div>
        <input type="text" class="search-box" id="search" placeholder="Search by name, email, ID number, type…" oninput="filterUsers()">
        <div class="results-row">
          <div class="results-info" id="results-info">Showing {{ total_users }} users</div>
          <div class="pick-hint" id="pick-hint">Pick a user to continue</div>
        </div>
        <div class="user-grid" id="user-grid">
          {% for u in user_list %}
          <div class="user-card" data-sub="{{ u.sub }}" data-search="{{ u.full_name|lower }} {{ u.email|lower }} {{ u.idnumber|lower }} {{ u.user_type_description|lower }} {{ u.first_name|lower }} {{ u.last_name|lower }} {{ u.first_name_dhivehi }}" onclick="selectUser('{{ u.sub }}', this)">
            <div class="name">{{ u.full_name or u.first_name + ' ' + (u.middle_name or '') + ' ' + u.last_name }}</div>
            <div class="meta">{{ u.email }} &middot; {{ u.idnumber }}</div>
            <span class="type {% if u.user_type_description == 'Maldivian' %}type-maldivian{% elif u.user_type_description == 'Work Permit Holder' %}type-workpermit{% else %}type-foreigner{% endif %}">{{ u.user_type_description }}</span>
          </div>
          {% endfor %}
        </div>
        <div class="no-results" id="no-results" style="display:none">No users match your search.</div>
      </section>

      <form method="post" id="select-form" class="panel-card settings-panel">
        {% for key, val in params.items() %}
        <input type="hidden" name="{{ key }}" value="{{ val }}">
        {% endfor %}
        <input type="hidden" name="action" value="select">
        <input type="hidden" name="sub" id="selected-sub" value="">
        <div class="panel-header">
          <div>
            <div class="panel-title">Authorize Request</div>
            <div class="panel-kicker">Configure scopes and redirect settings.</div>
          </div>
        </div>
        <div class="selected-info" id="selected-info"></div>
        <div class="settings-body">
          <div class="scope-box">
            <div class="scope-title">Scopes</div>
            <div class="scope-note">OpenID and eFaas profile are always included. Pick any additional scopes you want to request.</div>
            <div class="scope-grid">
              {% for scope, label, desc in scope_options %}
              <label class="scope-option {% if scope in selected_scopes and scope in ['openid', 'efaas.profile'] %}required{% endif %}">
                <input type="checkbox" data-scope-choice value="{{ scope }}" {% if scope in selected_scopes %}checked{% endif %} {% if scope in ['openid', 'efaas.profile'] %}disabled{% endif %}>
                <span><strong>{{ label }}</strong><small>{{ desc }}</small></span>
              </label>
              {% endfor %}
            </div>
            <input type="hidden" name="scope" class="scope-value" value="{{ selected_scope_value }}">
          </div>
          <div class="logout-box">
            <div class="scope-title">Redirect settings</div>
            <div class="scope-note">Optional. Save logout URLs so this session can be signed out from the mock UI.</div>
            <div class="logout-grid">
              <div class="full"><label>Back-channel logout URI</label><input name="backchannel_logout_uri" value="{{ params.backchannel_logout_uri }}" placeholder="https://your-site.example.com/backchannel/logout"></div>
              <div class="full"><label>Post logout redirect URI</label><input name="post_logout_redirect_uri" value="{{ params.post_logout_redirect_uri }}" placeholder="https://your-site.example.com/signed-out"></div>
            </div>
          </div>
        </div>
        <div class="actions"><button type="submit" class="btn btn-primary" id="btn-select" disabled>Sign In as Selected User</button></div>
      </form>
    </div>
  </div>

  <div id="panel-create" class="panel">
    <form method="post" id="create-form" class="auth-layout">
      {% for key, val in params.items() %}
      <input type="hidden" name="{{ key }}" value="{{ val }}">
      {% endfor %}
      <input type="hidden" name="action" value="create">
      <section class="panel-card account-panel">
        <div class="panel-header">
          <div>
            <div class="panel-title">Create New User</div>
            <div class="panel-kicker">New mock accounts are saved and reusable.</div>
          </div>
        </div>
        <div class="create-fields">
          <p class="create-intro">Fill in the details below, then use the settings panel to choose scopes before signing in.</p>
          <div class="form-grid">
            <div><label>First Name *</label><input name="first_name" required placeholder="Ahmed"></div>
            <div><label>Last Name *</label><input name="last_name" required placeholder="Rasheed"></div>
            <div><label>Middle Name</label><input name="middle_name" placeholder="Ali"></div>
            <div><label>Gender *</label><select name="gender" required><option value="M">Male</option><option value="F">Female</option></select></div>
            <div><label>First Name (Dhivehi)</label><input name="first_name_dhivehi" placeholder="އަހުމަދު"></div>
            <div><label>Last Name (Dhivehi)</label><input name="last_name_dhivehi" placeholder="ރަޝީދު"></div>
            <div><label>ID Number *</label><input name="idnumber" required placeholder="A123456"></div>
            <div><label>User Type *</label><select name="user_type_description" id="user-type" required onchange="toggleFields()"><option value="Maldivian">Maldivian</option><option value="Work Permit Holder">Work Permit Holder</option><option value="Foreigner">Foreigner</option></select></div>
            <div><label>Email *</label><input type="email" name="email" required placeholder="ahmed@example.com"></div>
            <div><label>Mobile *</label><input name="mobile" required placeholder="7912345"></div>
            <div><label>Birthdate *</label><input name="birthdate" required placeholder="6/3/1990" value="6/3/1990"></div>
            <div><label>Country</label><input name="country_name" id="country-name" value="Maldives" placeholder="Maldives"></div>
            <div id="passport-group" style="display:none"><label>Passport Number</label><input name="passport_number" placeholder="LA19E7432"></div>
            <div id="workpermit-group" style="display:none"><label>Work Permit Active</label><select name="is_workpermit_active"><option value="True">Yes</option><option value="False">No</option></select></div>
            <div class="full"><label>Permanent Address (JSON)</label><input name="permanent_address_json" placeholder='{"AddressLine1":"Blue Light","IslandName":"Male&apos;","Country":"Maldives",...}'></div>
          </div>
        </div>
      </section>
      <section class="panel-card settings-panel">
        <div class="panel-header">
          <div>
            <div class="panel-title">Authorize Request</div>
            <div class="panel-kicker">Configure scopes and redirect settings.</div>
          </div>
        </div>
        <div class="settings-body">
          <div class="scope-box">
            <div class="scope-title">Scopes</div>
            <div class="scope-note">OpenID and eFaas profile are always included. Pick any additional scopes you want to request.</div>
            <div class="scope-grid">
              {% for scope, label, desc in scope_options %}
              <label class="scope-option {% if scope in selected_scopes and scope in ['openid', 'efaas.profile'] %}required{% endif %}">
                <input type="checkbox" data-scope-choice value="{{ scope }}" {% if scope in selected_scopes %}checked{% endif %} {% if scope in ['openid', 'efaas.profile'] %}disabled{% endif %}>
                <span><strong>{{ label }}</strong><small>{{ desc }}</small></span>
              </label>
              {% endfor %}
            </div>
            <input type="hidden" name="scope" class="scope-value" value="{{ selected_scope_value }}">
          </div>
          <div class="logout-box">
            <div class="scope-title">Redirect settings</div>
            <div class="scope-note">Optional. Save logout URLs so this session can be signed out from the mock UI.</div>
            <div class="logout-grid">
              <div class="full"><label>Back-channel logout URI</label><input name="backchannel_logout_uri" value="{{ params.backchannel_logout_uri }}" placeholder="https://your-site.example.com/backchannel/logout"></div>
              <div class="full"><label>Post logout redirect URI</label><input name="post_logout_redirect_uri" value="{{ params.post_logout_redirect_uri }}" placeholder="https://your-site.example.com/signed-out"></div>
            </div>
          </div>
        </div>
        <div class="actions"><button type="submit" class="btn btn-primary">Create User &amp; Sign In</button></div>
      </section>
    </form>
  </div>

</div>

<script>
var selectedSub = null;
function switchTab(tab) {
  document.querySelectorAll('.tab').forEach(function(t,i){
    t.classList.toggle('active', (tab==='select'&&i===0)||(tab==='create'&&i===1));
  });
  document.getElementById('panel-select').classList.toggle('active', tab==='select');
  document.getElementById('panel-create').classList.toggle('active', tab==='create');
}
function selectUser(sub, el) {
  document.querySelectorAll('.user-card').forEach(function(c){ c.classList.remove('selected'); });
  el.classList.add('selected');
  document.getElementById('selected-sub').value = sub;
  document.getElementById('btn-select').disabled = false;
  selectedSub = sub;
  var u = el.querySelector('.name').textContent;
  document.getElementById('selected-info').innerHTML = '<strong>Selected:</strong> ' + u + ' (sub: ' + sub.substring(0,8) + '…)';
  document.getElementById('selected-info').classList.add('show');
}
function filterUsers() {
  var q = document.getElementById('search').value.toLowerCase();
  var cards = document.querySelectorAll('.user-card');
  var count = 0;
  cards.forEach(function(c){
    var match = c.getAttribute('data-search').indexOf(q) !== -1;
    c.style.display = match ? '' : 'none';
    if (match) count++;
  });
  document.getElementById('results-info').textContent = q ? 'Found ' + count + ' user(s)' : 'Showing {{ total_users }} users';
  document.getElementById('no-results').style.display = count === 0 ? '' : 'none';
  document.getElementById('pick-hint').style.display = count === 0 ? 'none' : '';
}
function toggleFields() {
  var t = document.getElementById('user-type').value;
  document.getElementById('passport-group').style.display = (t==='Work Permit Holder'||t==='Foreigner') ? '' : 'none';
  document.getElementById('workpermit-group').style.display = (t==='Work Permit Holder') ? '' : 'none';
}
function syncScopeValue(form) {
  var hidden = form.querySelector('.scope-value');
  var scopes = [];
  form.querySelectorAll('[data-scope-choice]').forEach(function(cb) {
    if (cb.checked || cb.disabled) scopes.push(cb.value);
  });
  hidden.value = Array.from(new Set(scopes)).join(' ');
}
function initScopePickers() {
  document.querySelectorAll('form').forEach(function(form) {
    var hidden = form.querySelector('.scope-value');
    if (!hidden) return;
    form.querySelectorAll('[data-scope-choice]').forEach(function(cb) {
      cb.addEventListener('change', function() { syncScopeValue(form); });
    });
    syncScopeValue(form);
  });
}
document.addEventListener('DOMContentLoaded', initScopePickers);
</script>
</body>
</html>"""

LOGOUT_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>eFaas Mock — Logout</title>
<style>
  :root { --navy: #1a237e; --border: #dfe3ea; --muted: #6b7280; --panel: rgba(255,255,255,.96); }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html, body { height: 100%; }
  body { font-family: -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; background: radial-gradient(circle at top left,#e8eaff 0,#f4f6fb 34%,#edf1f7 100%); color: #1f2937; min-height: 100vh; overflow: hidden; }
  .banner { min-height: 48px; background: linear-gradient(135deg,#1a237e,#283593); color: #fff; padding: 10px 24px; display: flex; align-items: center; justify-content: center; gap: 8px; text-align: center; font-size: 13px; }
  .banner strong { font-size: 16px; }
  .banner a { color: #fff; text-decoration: underline; margin-left: 8px; }
  .container { max-width: 1360px; height: calc(100vh - 48px); margin: 0 auto; padding: 14px 18px 18px; min-height: 0; }
  .logout-layout { display: grid; grid-template-columns: minmax(280px,.55fr) minmax(640px,1.7fr); gap: 14px; height: 100%; min-height: 0; }
  .panel-card { background: var(--panel); border: 1px solid var(--border); border-radius: 16px; box-shadow: 0 16px 40px rgba(31,41,55,.10); min-width: 0; min-height: 0; }
  .intro { padding: 18px; display: flex; flex-direction: column; justify-content: space-between; }
  .intro h1 { font-size: 24px; line-height: 1.05; margin-bottom: 8px; color: #111827; letter-spacing: -.02em; }
  .intro p { color: var(--muted); font-size: 13px; line-height: 1.5; }
  .intro-note { margin-top: 18px; padding: 12px; background: #eef2ff; border: 1px solid #cdd4ff; border-radius: 12px; color: var(--navy); font-size: 12px; font-weight: 700; }
  .sessions-panel { display: flex; flex-direction: column; padding: 14px; }
  .panel-header { flex: 0 0 auto; display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 10px; }
  .panel-title { font-size: 16px; font-weight: 800; color: #111827; }
  .panel-kicker { font-size: 12px; color: var(--muted); margin-top: 2px; }
  .count-pill { flex: 0 0 auto; border-radius: 999px; background: #eef2ff; color: var(--navy); padding: 5px 9px; font-size: 12px; font-weight: 800; }
  .session-grid { flex: 1; min-height: 0; display: grid; grid-template-columns: repeat(auto-fill,minmax(320px,1fr)); align-content: start; gap: 10px; overflow: auto; padding-right: 4px; }
  .session-card { min-width: 0; background: #fff; border-radius: 12px; padding: 12px; border: 1px solid #e4e7ee; }
  .session-title { font-size: 14px; font-weight: 800; color: var(--navy); margin-bottom: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .session-meta { font-size: 11px; color: var(--muted); margin-bottom: 10px; line-height: 1.35; word-break: break-word; }
  .session-card label { display: block; font-size: 12px; font-weight: 700; color: #4b5563; margin: 8px 0 4px; }
  .session-card input { width: 100%; padding: 8px 10px; border: 1px solid var(--border); border-radius: 8px; font-size: 13px; outline: none; transition: border-color .2s, box-shadow .2s; }
  .session-card input:focus { border-color: var(--navy); box-shadow: 0 0 0 3px rgba(26,35,126,.10); }
  .curl-sample { margin-top: 10px; }
  .curl-sample textarea { width: 100%; min-height: 84px; padding: 9px 10px; background: #f6f8fa; border-radius: 9px; border: 1px solid #e5e7eb; font-size: 11px; color: #1f2937; resize: vertical; font-family: ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,'Liberation Mono','Courier New',monospace; }
  .btn { display: inline-flex; align-items: center; justify-content: center; padding: 11px 16px; font-size: 13px; font-weight: 800; border: none; border-radius: 10px; cursor: pointer; transition: all .15s; }
  .btn-primary { background: var(--navy); color: #fff; width: 100%; margin-top: 10px; }
  .btn-primary:hover { background: #283593; transform: translateY(-1px); box-shadow: 0 8px 18px rgba(26,35,126,.25); }
  .empty { flex: 1; display: flex; align-items: center; justify-content: center; min-height: 240px; border: 1px dashed var(--border); border-radius: 12px; text-align: center; color: var(--muted); font-size: 14px; background: #fff; }
  @media (max-height: 720px) and (min-width: 901px) {
    .banner { min-height: 42px; padding: 8px 18px; }
    .container { height: calc(100vh - 42px); padding: 10px 14px 14px; }
    .intro { padding: 14px; }
    .intro-note { display: none; }
    .session-card { padding: 10px; }
    .curl-sample textarea { min-height: 72px; }
  }
  @media (max-width: 900px) {
    html, body { height: auto; }
    body { overflow: auto; }
    .banner { flex-wrap: wrap; }
    .container { height: auto; min-height: calc(100vh - 48px); padding: 12px; }
    .logout-layout { display: block; height: auto; }
    .panel-card { margin-bottom: 12px; }
    .session-grid { overflow: visible; grid-template-columns: 1fr; }
  }
</style>
</head>
<body>
<div class="banner">
  <strong>eFaas Mock Server</strong> — Back-channel logout tester.
  <a href="/">Status</a>
  <a href="/connect/authorize">Login</a>
</div>
<div class="container">
  <div class="logout-layout">
    <section class="panel-card intro">
      <div>
        <h1>Logout active sessions</h1>
        <p>Pick a session, adjust redirect or back-channel settings if needed, then dispatch a logout token from this mock server.</p>
      </div>
      <div class="intro-note">Back-channel logout calls are sent from this server using curl.</div>
    </section>
    <section class="panel-card sessions-panel">
      <div class="panel-header">
        <div>
          <div class="panel-title">Active Sessions</div>
          <div class="panel-kicker">Test logout behavior without leaving this screen.</div>
        </div>
        <div class="count-pill">{{ sessions|length }} active</div>
      </div>
      {% if sessions %}
      <div class="session-grid">
        {% for s in sessions %}
        <form class="session-card" method="post" action="/logout">
          <input type="hidden" name="id_token_hint" value="{{ s.id_token }}">
          <div class="session-title">{{ s.user_name }}</div>
          <div class="session-meta">ID Number: {{ s.user_idnumber }}<br>Client: {{ s.client_id }}<br>SID: {{ s.sid }}</div>
          <label>Back-channel logout URI</label>
          <input name="backchannel_logout_uri" value="{{ s.backchannel_logout_uri }}" placeholder="https://your-site.example.com/backchannel/logout">
          <label>Post logout redirect URI</label>
          <input name="post_logout_redirect_uri" value="{{ s.post_logout_redirect_uri }}" placeholder="https://your-site.example.com/signed-out">
          <label>State</label>
          <input name="state" value="{{ s.state }}" placeholder="optional state">
          <div class="curl-sample">
            <label>Sample curl request</label>
            <textarea readonly>{{ s.curl_command }}</textarea>
          </div>
          <button type="submit" class="btn btn-primary">Logout this session</button>
        </form>
        {% endfor %}
      </div>
      {% else %}
      <div class="empty">No active sessions yet. Sign in through the mock first.</div>
      {% endif %}
    </section>
  </div>
</div>
</body>
</html>"""

LOGOUT_RESULT_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>eFaas Mock — Logout Result</title>
<style>
  :root { --navy: #1a237e; --border: #dfe3ea; --muted: #6b7280; --panel: rgba(255,255,255,.96); }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { min-height: 100vh; padding: 24px; display: flex; align-items: center; justify-content: center; font-family: -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; background: radial-gradient(circle at top left,#e8eaff 0,#f4f6fb 34%,#edf1f7 100%); color: #1f2937; }
  .wrap { width: 100%; max-width: 760px; padding: 24px; background: var(--panel); border: 1px solid var(--border); border-radius: 18px; box-shadow: 0 16px 40px rgba(31,41,55,.10); }
  .badge { display: inline-flex; border-radius: 999px; background: #eef2ff; color: var(--navy); padding: 5px 9px; font-size: 12px; font-weight: 800; margin-bottom: 14px; }
  h1 { color: #111827; font-size: 28px; letter-spacing: -.02em; margin-bottom: 8px; }
  p { margin-top: 10px; line-height: 1.5; color: #374151; }
  .meta { color: var(--muted); font-size: 13px; word-break: break-word; padding: 10px 12px; background: #fff; border: 1px solid var(--border); border-radius: 10px; }
  .actions { display: flex; gap: 10px; margin-top: 18px; }
  .btn { display: inline-flex; align-items: center; justify-content: center; padding: 11px 16px; border-radius: 10px; background: var(--navy); color: #fff; text-decoration: none; font-size: 13px; font-weight: 800; transition: all .15s; }
  .btn:hover { background: #283593; transform: translateY(-1px); box-shadow: 0 8px 18px rgba(26,35,126,.25); }
</style>
</head>
<body>
<main class="wrap">
  <div class="badge">eFaas Mock Server</div>
  <h1>{{ title }}</h1>
  <p>{{ message }}</p>
  {% if backchannel_logout_uri %}<p class="meta">Back-channel URI: {{ backchannel_logout_uri }}</p>{% endif %}
  {% if post_logout_redirect_uri %}<p class="meta">Post logout redirect URI: {{ post_logout_redirect_uri }}</p>{% endif %}
  {% if error %}<p class="meta">Error: {{ error }}</p>{% endif %}
  <div class="actions"><a class="btn" href="/logout">Back to logout UI</a></div>
</main>
</body>
</html>"""

ERROR_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>eFaas Mock — Error</title>
<style>
  :root { --navy: #1a237e; --border: #dfe3ea; --muted: #6b7280; --panel: rgba(255,255,255,.96); }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { min-height: 100vh; padding: 24px; display: flex; align-items: center; justify-content: center; font-family: -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; background: radial-gradient(circle at top left,#e8eaff 0,#f4f6fb 34%,#edf1f7 100%); color: #1f2937; }
  .wrap { width: 100%; max-width: 720px; padding: 24px; background: var(--panel); border: 1px solid var(--border); border-radius: 18px; box-shadow: 0 16px 40px rgba(31,41,55,.10); }
  .badge { display: inline-flex; border-radius: 999px; background: #fff3e0; color: #e65100; padding: 5px 9px; font-size: 12px; font-weight: 800; margin-bottom: 14px; }
  h1 { color: #111827; font-size: 26px; letter-spacing: -.02em; margin-bottom: 8px; }
  p { margin-top: 10px; line-height: 1.5; color: #374151; }
  .detail { color: var(--muted); font-size: 13px; padding: 10px 12px; background: #fff; border: 1px solid var(--border); border-radius: 10px; }
  .actions { display: flex; gap: 10px; margin-top: 18px; }
  .btn { display: inline-flex; align-items: center; justify-content: center; padding: 11px 16px; border-radius: 10px; background: var(--navy); color: #fff; text-decoration: none; font-size: 13px; font-weight: 800; }
</style>
</head>
<body>
<main class="wrap">
  <div class="badge">HTTP {{ http_status }}</div>
  <h1>{{ message }}</h1>
  {% if detail %}<p class="detail">{{ detail }}</p>{% endif %}
  <div class="actions"><a class="btn" href="/connect/authorize">Back to login</a></div>
</main>
</body>
</html>"""

LOGOUT_REDIRECT_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>eFaas Mock \u2014 Signing Out</title>
<style>
  :root { --navy: #1a237e; --border: #dfe3ea; --muted: #6b7280; --panel: rgba(255,255,255,.96); }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { min-height: 100vh; padding: 24px; display: flex; align-items: center; justify-content: center; font-family: -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; background: radial-gradient(circle at top left,#e8eaff 0,#f4f6fb 34%,#edf1f7 100%); color: #1f2937; }
  .wrap { width: 100%; max-width: 760px; padding: 24px; background: var(--panel); border: 1px solid var(--border); border-radius: 18px; box-shadow: 0 16px 40px rgba(31,41,55,.10); }
  .badge { display: inline-flex; border-radius: 999px; background: #eef2ff; color: var(--navy); padding: 5px 9px; font-size: 12px; font-weight: 800; margin-bottom: 14px; }
  h1 { color: #111827; font-size: 28px; letter-spacing: -.02em; margin-bottom: 8px; }
  p { margin-top: 10px; line-height: 1.5; color: #374151; }
  .meta { color: var(--muted); font-size: 13px; word-break: break-word; padding: 10px 12px; background: #fff; border: 1px solid var(--border); border-radius: 10px; }
  .countdown { margin: 18px 0 10px; font-size: 14px; font-weight: 800; color: #1f2937; }
  .progress { margin-top: 10px; width: 100%; height: 10px; background: #e5e7eb; border-radius: 999px; overflow: hidden; }
  .progress-bar { height: 100%; width: 100%; background: linear-gradient(90deg, #1a237e, #3949ab); transform-origin: left center; transition: width .2s linear; }
  .actions { display: flex; gap: 10px; margin-top: 18px; }
  .btn { display: inline-flex; align-items: center; justify-content: center; padding: 11px 16px; border-radius: 10px; background: var(--navy); color: #fff; text-decoration: none; font-size: 13px; font-weight: 800; transition: all .15s; }
  .btn:hover { background: #283593; transform: translateY(-1px); box-shadow: 0 8px 18px rgba(26,35,126,.25); }
</style>
</head>
<body>
<main class="wrap">
  <div class="badge">eFaas Mock Server</div>
  <h1>{{ title }}</h1>
  <p>{{ message }}</p>
  {% if backchannel_logout_uri %}<p class="meta">Back-channel URI: {{ backchannel_logout_uri }}</p>{% endif %}
  <p class="meta">Redirecting to: {{ redirect_url }}</p>
  <div class="countdown">Redirecting in <span id="countdown">15</span> seconds...</div>
  <div class="progress"><div id="progress-bar" class="progress-bar"></div></div>
  <div class="actions"><a class="btn" href="{{ redirect_url }}">Continue</a></div>
</main>
<script>
  window.addEventListener('load', function () {
    var redirectUrl = {{ redirect_url_json }};
    var totalSeconds = 15;
    var remainingSeconds = totalSeconds;
    var countdownEl = document.getElementById('countdown');
    var progressBarEl = document.getElementById('progress-bar');

    function renderCountdown() {
      countdownEl.textContent = String(remainingSeconds);
      progressBarEl.style.width = ((remainingSeconds / totalSeconds) * 100) + '%';
    }

    renderCountdown();

    var timer = window.setInterval(function () {
      remainingSeconds -= 1;
      renderCountdown();
      if (remainingSeconds <= 0) {
        window.clearInterval(timer);
        window.location.replace(redirectUrl);
      }
    }, 1000);
  });
</script>
</body>
</html>"""

AUTO_POST_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>eFaas Mock — Redirecting…</title>
<style>
  :root { --navy: #1a237e; --border: #dfe3ea; --muted: #6b7280; --panel: rgba(255,255,255,.96); }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { min-height: 100vh; padding: 24px; display: flex; align-items: center; justify-content: center; font-family: -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; background: radial-gradient(circle at top left,#e8eaff 0,#f4f6fb 34%,#edf1f7 100%); color: #1f2937; }
  .wrap { width: 100%; max-width: 520px; padding: 24px; background: var(--panel); border: 1px solid var(--border); border-radius: 18px; box-shadow: 0 16px 40px rgba(31,41,55,.10); text-align: center; }
  .badge { display: inline-flex; border-radius: 999px; background: #eef2ff; color: var(--navy); padding: 5px 9px; font-size: 12px; font-weight: 800; margin-bottom: 14px; }
  h1 { color: #111827; font-size: 26px; letter-spacing: -.02em; margin-bottom: 8px; }
  p { color: var(--muted); font-size: 14px; line-height: 1.5; }
  .progress { margin-top: 18px; width: 100%; height: 10px; background: #e5e7eb; border-radius: 999px; overflow: hidden; }
  .progress-bar { height: 100%; width: 45%; background: linear-gradient(90deg, #1a237e, #3949ab); border-radius: inherit; animation: loading 1.1s ease-in-out infinite alternate; }
  @keyframes loading { from { transform: translateX(-80%); } to { transform: translateX(180%); } }
</style>
</head>
<body onload="document.getElementById('cb').submit()">
  <main class="wrap">
    <div class="badge">eFaas Mock Server</div>
    <h1>Signing in</h1>
    <p>Signing in, please wait…</p>
    <div class="progress"><div class="progress-bar"></div></div>
  </main>
  <form id="cb" method="post" action="{{ redirect_uri }}">
    <input type="hidden" name="code" value="{{ code }}">
    <input type="hidden" name="id_token" value="{{ id_token }}">
    <input type="hidden" name="scope" value="{{ scope }}">
    <input type="hidden" name="session_state" value="{{ session_state }}">
    {% if state %}<input type="hidden" name="state" value="{{ state }}">{% endif %}
  </form>
</body>
</html>"""
