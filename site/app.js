let allSkills = [];
let activePlatforms = new Set();
let activeRepo = '';
let searchQuery = '';

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
    <div class="skill-repo">${escapeHtml(skill.repo)}</div>
    <div class="badges">${badges}</div>
    <div class="skill-meta">${meta}</div>
    <a class="skill-link" href="${escapeHtml(skill.url)}" target="_blank" rel="noopener noreferrer">→ View skill</a>
  `;
  return card;
}

function render() {
  const filtered = filter(allSkills);
  document.getElementById('result-count').textContent =
    `Showing ${filtered.length.toLocaleString()} of ${allSkills.length.toLocaleString()} skills`;
  const grid = document.getElementById('skills-grid');
  grid.innerHTML = '';
  if (filtered.length === 0) {
    grid.innerHTML = '<div class="empty-state">No skills match your filters.</div>';
    return;
  }
  const fragment = document.createDocumentFragment();
  filtered.forEach(skill => fragment.appendChild(renderCard(skill)));
  grid.appendChild(fragment);
}

init();
