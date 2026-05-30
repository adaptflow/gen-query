/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  docsSidebar: [
    'intro',
    {
      type: 'category',
      label: 'Getting Started',
      items: [
        'getting-started/installation',
        'getting-started/quick-start',
        'getting-started/cli',
      ],
    },
    {
      type: 'category',
      label: 'Core Concepts',
      items: [
        'core-concepts/architecture',
        'core-concepts/pipeline',
        'core-concepts/query-result',
      ],
    },
    {
      type: 'category',
      label: 'Usage',
      items: [
        'usage/sync-api',
        'usage/async-api',
        'usage/dry-run',
        'usage/streaming',
        'usage/configuration',
        'usage/logging',
      ],
    },
    {
      type: 'category',
      label: 'LLM Adapters',
      items: ['llm-adapters/overview'],
    },
    {
      type: 'category',
      label: 'Databases',
      items: ['databases/supported-databases'],
    },
    {
      type: 'category',
      label: 'Security',
      items: ['security/overview'],
    },
    {
      type: 'category',
      label: 'Customization',
      items: [
        'customization/custom-pipeline-stages',
        'customization/callbacks',
      ],
    },
    {
      type: 'category',
      label: 'Examples',
      items: ['examples/fastapi'],
    },
    {
      type: 'category',
      label: 'API Reference',
      items: [
        'api-reference/overview',
        'api-reference/genquery',
        'api-reference/async-genquery',
        'api-reference/query-result',
        'api-reference/configuration',
        'api-reference/models',
        'api-reference/llm-adapters',
        'api-reference/callbacks',
        'api-reference/pipeline',
        'api-reference/logging',
      ],
    },
  ],
};

module.exports = sidebars;
