window.REPO_META = {
  githubOwner: "huskydoge",
  defaultRepoName: "Awesome-Loop-Models",
  publicRepoName: "Awesome-Loop-Models",
  publicPagesBase: "https://huskydoge.github.io/Awesome-Loop-Models",
  inferRepoNameFromLocation(locationLike = window.location) {
    const pathParts = String(locationLike.pathname || '').split('/').filter(Boolean);
    const hostname = String(locationLike.hostname || '');
    if (hostname.endsWith('github.io') && pathParts.length) return pathParts[0];
    if (hostname === 'github.com' && pathParts.length >= 2) return pathParts[1];
    return this.defaultRepoName;
  },
  getGitHubRepoBase(locationLike = window.location) {
    return 'https://github.com/' + this.githubOwner + '/' + this.inferRepoNameFromLocation(locationLike);
  },
  getGitHubBlobUrl(path, locationLike = window.location) {
    return this.getGitHubRepoBase(locationLike) + '/blob/main/' + String(path || '').replace(/^\/+/, '');
  },
  getGitHubNewFileBase(locationLike = window.location) {
    return this.getGitHubRepoBase(locationLike) + '/new/main';
  }
};
