let allSkills = [];
let activePlatforms = new Set();
let activeRepo = '';
let searchQuery = '';
let viewMode = 'cards';
let activeCategory = 'dev_tool';

async function init() {
  const resp = await fetch('skills.json');
  const data = await resp.json();
  allSkills = data.skills;

  const updated = new Date(data.generated_at);
  document.getElementById('last-updated').textContent =
    `Last updated: ${updated.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })}`;

  const repoCount = new Set(data.skills.map(s => s.repo)).size;
  document.getElementById('stats').textContent =
    `${data.total.toLocaleString()} skills across ${repoCount} repos`;

  const repos = [...new Set(data.skills.map(s => s.repo))].sort();
  const select = document.getElementById('repo-filter');
  repos.forEach(repo => {
    const opt = document.createElement('option');
    opt.value = repo;
    opt.textContent = repo;
    select.appendChild(opt);
  });

  document.getElementById('search').addEventListener('input', e => {
    searchQuery = e.target.value.toLowerCase();
    render();
  });

  document.getElementById('repo-filter').addEventListener('change', e => {
    activeRepo = e.target.value;
    render();
  });

  document.querySelectorAll('.toggle[data-platform]').forEach(btn => {
    btn.addEventListener('click', () => {
      const platform = btn.dataset.platform;
      if (platform === 'all') {
        activePlatforms.clear();
        document.querySelectorAll('.toggle').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
      } else {
        document.querySelector('.toggle[data-platform="all"]').classList.remove('active');
        btn.classList.toggle('active');
        if (btn.classList.contains('active')) {
          activePlatforms.add(platform);
        } else {
          activePlatforms.delete(platform);
        }
        if (activePlatforms.size === 0) {
          document.querySelector('.toggle[data-platform="all"]').classList.add('active');
        }
      }
      render();
    });
  });

  document.querySelectorAll('.toggle[data-category]').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.toggle[data-category]').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      activeCategory = btn.dataset.category;
      render();
    });
  });

  document.getElementById('view-cards').addEventListener('click', () => {
    viewMode = 'cards';
    document.getElementById('view-cards').classList.add('active');
    document.getElementById('view-table').classList.remove('active');
    render();
  });

  document.getElementById('view-table').addEventListener('click', () => {
    viewMode = 'table';
    document.getElementById('view-table').classList.add('active');
    document.getElementById('view-cards').classList.remove('active');
    render();
  });

  render();
}

function filter(skills) {
  return skills.filter(skill => {
    if (searchQuery &&
        !skill.name.toLowerCase().includes(searchQuery) &&
        !skill.description.toLowerCase().includes(searchQuery)) {
      return false;
    }
    if (activeRepo && skill.repo !== activeRepo) return false;
    if (activePlatforms.size > 0) {
      for (const p of activePlatforms) {
        if (!skill.platforms.includes(p)) return false;
      }
    }
    if (activeCategory !== 'all' && (skill.category || 'unclear') !== activeCategory) return false;
    return true;
  });
}

function relativeDate(dateStr) {
  if (!dateStr) return 'Unknown';
  const days = Math.floor((Date.now() - new Date(dateStr)) / 86400000);
  if (days === 0) return 'Today';
  if (days === 1) return 'Yesterday';
  if (days < 7) return `${days}d ago`;
  if (days < 30) return `${Math.floor(days / 7)}w ago`;
  return `${Math.floor(days / 30)}mo ago`;
}

function escapeHtml(str) {
  return String(str ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
}

const CATEGORY_LABELS = { dev_tool: 'Dev Tool', feature: 'Feature', unclear: 'Unclear' };

function categoryBadge(skill) {
  const cat = skill.category || 'unclear';
  return `<span class="badge badge-category badge-${cat}">${CATEGORY_LABELS[cat] || cat}</span>`;
}

function renderCard(skill) {
  const card = document.createElement('div');
  card.className = 'skill-card';
  const badges = skill.platforms.length
    ? skill.platforms.map(p => `<span class="badge">${escapeHtml(p)}</span>`).join('')
    : '';
  const meta = [
    `Updated ${relativeDate(skill.last_updated)}`,
    skill.author ? `by ${escapeHtml(skill.author)}` : '',
  ].filter(Boolean).join(' ');

  card.innerHTML = `
    <div class="skill-name">${escapeHtml(skill.name)}</div>
    <div class="skill-description">${escapeHtml(skill.description)}</div>
    <div class="badges">${categoryBadge(skill)}${badges}</div>
    <div class="skill-meta">${meta}</div>
    <a class="skill-link" href="${escapeHtml(skill.url)}" target="_blank" rel="noopener noreferrer">→ View skill</a>
  `;
  return card;
}

function groupByRepo(filtered) {
  const grouped = {};
  filtered.forEach(skill => {
    if (!grouped[skill.repo]) grouped[skill.repo] = [];
    grouped[skill.repo].push(skill);
  });
  return Object.keys(grouped).sort().map(repo => ({ repo, skills: grouped[repo] }));
}

function renderTable(filtered) {
  if (filtered.length === 0) {
    return '<div class="empty-table">No skills match your filters.</div>';
  }
  let tbody = '';
  groupByRepo(filtered).forEach(({ repo, skills }) => {
    tbody += `<tr class="repo-group-row"><td colspan="5">${escapeHtml(repo)}</td></tr>`;
    skills.forEach(skill => {
      const badges = skill.platforms.map(p => `<span class="badge">${escapeHtml(p)}</span>`).join(' ');
      tbody += `<tr>
        <td class="col-name">${escapeHtml(skill.name)}</td>
        <td class="col-desc">${escapeHtml(skill.description)}</td>
        <td class="col-platforms">${categoryBadge(skill)} ${badges}</td>
        <td class="col-updated">${relativeDate(skill.last_updated)}</td>
        <td class="col-link"><a href="${escapeHtml(skill.url)}" target="_blank" rel="noopener noreferrer">View →</a></td>
      </tr>`;
    });
  });
  return `<table class="skills-table">
    <thead><tr>
      <th>Name</th>
      <th>Description</th>
      <th>Platform</th>
      <th>Updated</th>
      <th></th>
    </tr></thead>
    <tbody>${tbody}</tbody>
  </table>`;
}

function render() {
  const filtered = filter(allSkills);
  document.getElementById('result-count').textContent =
    `Showing ${filtered.length.toLocaleString()} of ${allSkills.length.toLocaleString()} skills`;
  const container = document.getElementById('skills-grid');
  container.className = '';
  container.innerHTML = '';

  if (viewMode === 'table') {
    container.innerHTML = renderTable(filtered);
    return;
  }

  if (filtered.length === 0) {
    container.innerHTML = '<div class="empty-state">No skills match your filters.</div>';
    return;
  }

  const fragment = document.createDocumentFragment();
  groupByRepo(filtered).forEach(({ repo, skills }) => {
    const section = document.createElement('div');
    section.className = 'repo-group';

    const heading = document.createElement('h2');
    heading.className = 'repo-group-heading';
    heading.textContent = repo;
    section.appendChild(heading);

    const grid = document.createElement('div');
    grid.className = 'skills-grid';
    skills.forEach(skill => grid.appendChild(renderCard(skill)));
    section.appendChild(grid);

    fragment.appendChild(section);
  });
  container.appendChild(fragment);
}

init();
