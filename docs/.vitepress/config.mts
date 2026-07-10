import { defineConfig } from 'vitepress'
import { withMermaid } from 'vitepress-plugin-mermaid'
import { generateSidebar } from './sidebar.mjs'

export default withMermaid(defineConfig({
  title: 'Meiso Glass',
  description: 'Two-part embedded sensing and display system',
  base: process.env.GITHUB_ACTIONS ? '/meiso_glass/' : '/',
  cleanUrls: true,
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
      message: 'Meiso Glass system, link, and validation specifications.',
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
