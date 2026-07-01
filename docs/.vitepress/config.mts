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
          { text: 'SDK 索引', link: '/SDK/' },
          { text: '设计总览', link: '/SDK/bible/SDK_DESIGN_OVERVIEW' }
        ]
      },
      {
        text: 'Spec',
        items: [
          { text: 'Spec 索引', link: '/spec/' },
          { text: '运行平面', link: '/spec/runtime-planes' },
          { text: 'SDK 公开面', link: '/spec/sdk-surface' },
          { text: '渲染能力等级', link: '/spec/render-profile' },
          { text: '对象协议', link: '/spec/object-protocol' },
          { text: 'Runtime 协议', link: '/spec/runtime-protocol' },
          { text: 'Wire 协议', link: '/spec/wire-protocol' },
          { text: '传输 Profile', link: '/spec/transport-profile' },
          { text: 'Wire 测试向量', link: '/spec/wire-test-vectors' },
          { text: '能力 Profile', link: '/spec/capability-profile' },
          { text: '状态机', link: '/spec/state-machines' },
          { text: '时间模型', link: '/spec/time-model' },
          { text: '安全策略', link: '/spec/security-policy' },
          { text: '故障模型', link: '/spec/fault-model' }
        ]
      },
      {
        text: 'Standards',
        items: [
          { text: '编码规范', link: '/standards/coding-standard' },
          { text: '语言策略', link: '/standards/language-policy' }
        ]
      },
      {
        text: 'Development',
        items: [
          { text: '环境', link: '/development/environment' },
          { text: '本地冒烟测试', link: '/development/local-smoke-tests' },
          { text: '硬件验证', link: '/development/hardware-validation' }
        ]
      },
      {
        text: 'CI/CD',
        items: [
          { text: '总览', link: '/ci-cd/' }
        ]
      },
      {
        text: 'Decisions',
        items: [
          { text: '总览', link: '/decisions/' },
          { text: 'Core Wire Transport', link: '/decisions/0001-core-wire-transport' },
          { text: 'Remove AI Native Interface', link: '/decisions/0002-remove-ai-native-interface' }
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
