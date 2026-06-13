import { defineConfig } from 'vitepress'
import { withMermaid } from 'vitepress-plugin-mermaid'

export default withMermaid(defineConfig({
  title: 'Meiso Glass',
  description: 'Open dual-device AR glasses SDK wiki',
  cleanUrls: true,
  srcExclude: [
    '**/.DS_Store',
    'SDK/bible/meiso_sdk_bible_*/**',
    'SDK/bible/meiso_sdk_bible_*.zip'
  ],
  themeConfig: {
    logo: '/logo.svg',
    search: {
      provider: 'local'
    },
    nav: [
      { text: 'Guide', link: '/guide/introduction' },
      { text: 'SDK Bible', link: '/SDK/bible/SDK_DESIGN_OVERVIEW' },
      { text: 'Validation', link: '/validation/' },
      { text: 'Origin', link: '/origin/' }
    ],
    sidebar: {
      '/guide/': [
        {
          text: 'Guide',
          items: [
            { text: 'Introduction', link: '/guide/introduction' },
            { text: 'Architecture Map', link: '/guide/architecture-map' },
            { text: 'Diagram Rendering', link: '/guide/diagram-rendering' },
            { text: 'Maintenance Loop', link: '/guide/maintenance-loop' }
          ]
        }
      ],
      '/SDK/': [
        {
          text: 'SDK Bible',
          items: [
            { text: 'SDK Index', link: '/SDK/' },
            { text: 'Design Overview', link: '/SDK/bible/SDK_DESIGN_OVERVIEW' },
            { text: 'Subsystem Design', link: '/SDK/bible/SDK_SUBSYSTEM_DESIGN' },
            { text: 'Development Plan', link: '/SDK/bible/SDK_DEVELOPMENT_PLAN' }
          ]
        }
      ],
      '/validation/': [
        {
          text: 'Validation',
          items: [
            { text: 'Validation Plan', link: '/validation/' }
          ]
        }
      ],
      '/origin/': [
        {
          text: 'Origin',
          items: [
            { text: 'Origin Index', link: '/origin/' },
            { text: 'Hardware Sketch', link: '/origin/dev_hardware_sketch' },
            { text: 'Peripheral Validation Board', link: '/origin/endpoint_peripheral_validation_board' }
          ]
        }
      ]
    },
    socialLinks: [
      { icon: 'github', link: 'https://github.com/anantheparty/meiso_glass' }
    ],
    outline: {
      level: [2, 3]
    },
    editLink: {
      pattern: 'https://github.com/anantheparty/meiso_glass/edit/main/docs/:path',
      text: 'Edit this page'
    },
    footer: {
      message: 'Maintained as the public-facing wiki for the Meiso Glass SDK.',
      copyright: 'Meiso Glass'
    }
  },
  mermaid: {
    securityLevel: 'strict',
    startOnLoad: false,
    theme: 'neutral'
  },
  mermaidPlugin: {
    class: 'meiso-mermaid'
  }
}))
