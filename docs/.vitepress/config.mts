import { defineConfig } from 'vitepress'
import { withMermaid } from 'vitepress-plugin-mermaid'
import { generateSidebar } from './sidebar.mjs'

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
    sidebar: generateSidebar(),
    socialLinks: [
      { icon: 'github', link: 'https://github.com/anantheparty/meiso_glass' }
    ],
    outline: {
      level: [2, 3]
    },
    editLink: {
      pattern: 'https://github.com/anantheparty/meiso_glass/edit/main/docs/:path',
      text: '编辑此页'
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
