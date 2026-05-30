// @ts-check

const lightCodeTheme = require('prism-react-renderer').themes.github;
const darkCodeTheme = require('prism-react-renderer').themes.dracula;

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'GenQuery',
  tagline: 'Agentic Natural Language to SQL for Python',
  url: 'https://adaptflow.github.io',
  baseUrl: '/gen-query',
  trailingSlash: false,
  organizationName: 'adaptflow',
  projectName: 'gen-query',

  onBrokenLinks: 'throw',

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  themes: [
    '@docusaurus/theme-mermaid',
  ],
  markdown: {
    mermaid: true,
    hooks: {
      onBrokenMarkdownLinks: 'warn',
    },
  },

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          sidebarPath: require.resolve('./sidebars.js'),
          editUrl: 'https://github.com/adaptflow/gen-query/tree/main/docs/',
        },
        blog: false,
        theme: {
          customCss: require.resolve('./src/css/custom.css'),
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      navbar: {
        title: 'GenQuery',
        items: [
          {
            type: 'docSidebar',
            sidebarId: 'docsSidebar',
            position: 'left',
            label: 'Docs',
          },
          {
            to: '/docs/getting-started/quick-start',
            label: 'Quick Start',
            position: 'left',
          },
          {
            to: '/docs/getting-started/cli',
            label: 'CLI',
            position: 'left',
          },
          {
            href: 'https://pypi.org/project/genquery/',
            label: 'PyPI',
            position: 'right',
          },
          {
            href: 'https://github.com/adaptflow/gen-query',
            label: 'GitHub',
            position: 'right',
          },
        ],
      },
      footer: {
        style: 'dark',
        links: [
          {
            title: 'Docs',
            items: [
              { label: 'Introduction', to: '/docs/intro' },
              { label: 'Installation', to: '/docs/getting-started/installation' },
              { label: 'Configuration', to: '/docs/usage/configuration' },
              { label: 'Security', to: '/docs/security/overview' },
            ],
          },
          {
            title: 'Project',
            items: [
              { label: 'PyPI', href: 'https://pypi.org/project/genquery/' },
              { label: 'GitHub', href: 'https://github.com/adaptflow/gen-query' },
              { label: 'Issues', href: 'https://github.com/adaptflow/gen-query/issues' },
            ],
          },
        ],
        copyright: `Copyright © ${new Date().getFullYear()} GenQuery. Built with Docusaurus.`,
      },
      prism: {
        theme: lightCodeTheme,
        darkTheme: darkCodeTheme,
        additionalLanguages: ['python', 'bash', 'yaml', 'sql'],
      },
    }),
};

module.exports = config;
