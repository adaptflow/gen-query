// @ts-check

const lightCodeTheme = require('prism-react-renderer').themes.github;
const darkCodeTheme = require('prism-react-renderer').themes.dracula;

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'GenQuery',
  tagline: 'Agentic Natural Language to SQL for Python',
  url: 'https://genquery.dev',
  baseUrl: '/',

  organizationName: 'genquery',
  projectName: 'genquery',

  onBrokenLinks: 'throw',
  markdown: {
    hooks: {
      onBrokenMarkdownLinks: 'warn',
    },
  },

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          sidebarPath: require.resolve('./sidebars.js'),
          editUrl: 'https://github.com/genquery/genquery/tree/main/website/',
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
            href: 'https://github.com/genquery/genquery',
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
              { label: 'GitHub', href: 'https://github.com/genquery/genquery' },
              { label: 'Issues', href: 'https://github.com/genquery/genquery/issues' },
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
