LOGIN_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>eFaas Mock — Login</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; background: #f0f2f5; color: #333; min-height: 100vh; }
  .banner { background: linear-gradient(135deg,#1a237e,#283593); color: #fff; padding: 16px 24px; text-align: center; font-size: 13px; }
  .banner strong { font-size: 16px; }
  .container { max-width: 960px; margin: 0 auto; padding: 24px 16px; }
  .tabs { display: flex; gap: 4px; margin-bottom: 24px; }
  .tab { flex: 1; padding: 12px; text-align: center; background: #e8eaed; border-radius: 8px 8px 0 0; cursor: pointer; font-weight: 600; font-size: 14px; transition: background .2s; user-select: none; }
  .tab.active { background: #fff; color: #1a237e; }
  .tab:hover:not(.active) { background: #d2d5d9; }
  .panel { display: none; background: #fff; border-radius: 0 0 12px 12px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,.08); }
  .panel.active { display: block; }
  .search-box { width: 100%; padding: 12px 16px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 14px; margin-bottom: 16px; outline: none; transition: border-color .2s; }
  .search-box:focus { border-color: #1a237e; }
  .user-grid { display: grid; grid-template-columns: repeat(auto-fill,minmax(280px,1fr)); gap: 10px; max-height: 440px; overflow-y: auto; padding-right: 4px; }
  .user-card { border: 2px solid #e8eaed; border-radius: 8px; padding: 12px 14px; cursor: pointer; transition: all .15s; }
  .user-card:hover { border-color: #1a237e; background: #f5f6ff; box-shadow: 0 1px 6px rgba(26,35,126,.08); }
  .user-card.selected { border-color: #1a237e; background: #e8eaff; }
  .user-card .name { font-weight: 600; font-size: 14px; }
  .user-card .meta { font-size: 12px; color: #666; margin-top: 2px; }
  .user-card .type { display: inline-block; font-size: 11px; padding: 2px 8px; border-radius: 10px; margin-top: 4px; }
  .type-maldivian { background: #e8f5e9; color: #2e7d32; }
  .type-workpermit { background: #fff3e0; color: #e65100; }
  .type-foreigner { background: #e3f2fd; color: #1565c0; }
  .results-info { font-size: 13px; color: #888; margin-bottom: 10px; }
  .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px 16px; }
  .form-grid .full { grid-column: 1 / -1; }
  label { display: block; font-size: 13px; font-weight: 600; color: #555; margin-bottom: 4px; }
  input, select { width: 100%; padding: 10px 12px; border: 2px solid #e0e0e0; border-radius: 6px; font-size: 14px; outline: none; transition: border-color .2s; }
  input:focus, select:focus { border-color: #1a237e; }
  .btn { display: inline-flex; align-items: center; justify-content: center; padding: 12px 24px; font-size: 14px; font-weight: 600; border: none; border-radius: 8px; cursor: pointer; transition: all .15s; }
  .btn-primary { background: #1a237e; color: #fff; width: 100%; margin-top: 8px; }
  .btn-primary:hover { background: #283593; transform: translateY(-1px); box-shadow: 0 2px 8px rgba(26,35,126,.3); }
  .actions { display: flex; gap: 10px; margin-top: 20px; }
  .actions .btn { flex: 1; }
  .subtitle { font-size: 13px; color: #888; margin-bottom: 20px; }
  .no-results { text-align: center; padding: 40px; color: #999; font-size: 14px; }
  .pick-hint { font-size: 13px; color: #888; margin-bottom: 16px; text-align: center; }
  .selected-info { background: #e8eaff; border: 2px solid #1a237e; border-radius: 8px; padding: 10px 14px; margin-top: 14px; font-size: 13px; display: none; }
  .selected-info.show { display: block; }
</style>
</head>
<body>
<div class="banner">
  <strong>eFaas Mock Server</strong> — Development only. No real authentication.
</div>
<div class="container">

  <div class="tabs">
    <div class="tab active" onclick="switchTab('select')">Select Existing User <small>({{ total_users }})</small></div>
    <div class="tab" onclick="switchTab('create')">Create New User</div>
  </div>

  <div id="panel-select" class="panel active">
    <input type="text" class="search-box" id="search" placeholder="Search by name, email, ID number, type…" oninput="filterUsers()">
    <div class="results-info" id="results-info">Showing {{ total_users }} users</div>
    <div class="pick-hint" id="pick-hint">Select a user below, then click <strong>Sign In as Selected User</strong></div>
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

    <div class="selected-info" id="selected-info"></div>

    <form method="post" id="select-form">
      {% for key, val in params.items() %}
      <input type="hidden" name="{{ key }}" value="{{ val }}">
      {% endfor %}
      <input type="hidden" name="action" value="select">
      <input type="hidden" name="sub" id="selected-sub" value="">
      <button type="submit" class="btn btn-primary" id="btn-select" disabled>Sign In as Selected User</button>
    </form>
  </div>

  <div id="panel-create" class="panel">
    <p class="subtitle">Fill in the details below to create a new account. All new accounts are saved and reusable.</p>
    <form method="post" id="create-form">
      {% for key, val in params.items() %}
      <input type="hidden" name="{{ key }}" value="{{ val }}">
      {% endfor %}
      <input type="hidden" name="action" value="create">
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
      <div class="actions"><button type="submit" class="btn btn-primary">Create User &amp; Sign In</button></div>
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
</script>
</body>
</html>"""

AUTO_POST_TEMPLATE = """<!DOCTYPE html>
<html>
<head><title>eFaas Mock — Redirecting…</title></head>
<body onload="document.getElementById('cb').submit()">
  <p style="font-family:sans-serif;text-align:center;padding-top:40px">Signing in, please wait…</p>
  <form id="cb" method="post" action="{{ redirect_uri }}">
    <input type="hidden" name="code" value="{{ code }}">
    <input type="hidden" name="id_token" value="{{ id_token }}">
    <input type="hidden" name="scope" value="{{ scope }}">
    <input type="hidden" name="session_state" value="{{ session_state }}">
    {% if state %}<input type="hidden" name="state" value="{{ state }}">{% endif %}
  </form>
</body>
</html>"""
