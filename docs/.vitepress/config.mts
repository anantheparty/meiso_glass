import { defineConfig } from 'vitepress'
import { withMermaid } from 'vitepress-plugin-mermaid'

export default withMermaid(defineConfig({
  title: 'Meiso Glass',
  description: 'Open dual-device AR glasses SDK wiki',
  base: process.env.GITHUB_ACTIONS ? '/meiso_glass/' : '/',
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
    nav: [],
    sidebar: [
      {
        text: 'Bible',
        items: [
          { text: 'SDK Index', link: '/SDK/' },
          { text: 'Design Overview', link: '/SDK/bible/SDK_DESIGN_OVERVIEW' }
        ]
      },
      {
        text: 'API',
        items: [
          { text: 'Spec', link: '/api/spec' },
          { text: 'AI Native API', link: '/api/ai-native' }
        ]
      },
      {
        text: 'Standards',
        items: [
          { text: 'Coding Standard', link: '/standards/coding-standard' }
        ]
      },
      {
        text: 'Development',
        items: [
          { text: 'Environment', link: '/development/environment' },
          { text: 'Local Smoke Tests', link: '/development/local-smoke-tests' },
          { text: 'Hardware Validation', link: '/development/hardware-validation' }
        ]
      },
      {
        text: 'CI/CD',
        items: [
          { text: 'Overview', link: '/ci-cd/' }
        ]
      }
    ],
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
