import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const CONFIG_DIR = path.dirname(fileURLToPath(import.meta.url))
const DEFAULT_DOCS_ROOT = path.resolve(CONFIG_DIR, '..')

const TOP_LEVEL_ORDER = [
  'SDK',
  'spec',
  'standards',
  'development',
  'ci-cd',
  'decisions',
  'origin'
]

const TOP_LEVEL_LABELS = new Map([
  ['SDK', 'SDK'],
  ['spec', 'Spec'],
  ['standards', 'Standards'],
  ['development', 'Development'],
  ['ci-cd', 'CI/CD'],
  ['decisions', 'Decisions'],
  ['origin', 'Origin']
])

const DIRECTORY_LABELS = new Map([
  ['bible', 'Bible']
])

const EXCLUDED_TOP_LEVEL = new Set(['.vitepress', 'public'])
const EXCLUDED_MARKDOWN_FILES = new Set(['README.md'])

const collator = new Intl.Collator('en', {
  numeric: true,
  sensitivity: 'base'
})

export function generateSidebar(options = {}) {
  const docsRoot = path.resolve(options.docsRoot ?? DEFAULT_DOCS_ROOT)

  return listDirectories(docsRoot)
    .filter((entry) => isTopLevelContentDirectory(entry.name))
    .sort((left, right) => compareTopLevel(left.name, right.name))
    .map((entry) => buildDirectoryGroup(docsRoot, entry.name))
    .filter((group) => group.items.length > 0)
}

export function collectSidebarLinks(sidebar) {
  const links = []

  for (const item of sidebar) {
    collectLinks(item, links)
  }

  return links
}

export function discoverSidebarPageLinks(options = {}) {
  const docsRoot = path.resolve(options.docsRoot ?? DEFAULT_DOCS_ROOT)
  const links = []

  for (const section of listDirectories(docsRoot).filter((entry) => isTopLevelContentDirectory(entry.name))) {
    collectMarkdownLinks(docsRoot, section.name, links)
  }

  return links.sort(compareLinks)
}

function buildDirectoryGroup(docsRoot, relativeDir) {
  const absoluteDir = path.join(docsRoot, relativeDir)
  const items = []
  const indexPath = path.join(absoluteDir, 'index.md')

  if (fs.existsSync(indexPath)) {
    items.push({
      text: '总览',
      link: linkForMarkdownPath(relativeDir, 'index.md')
    })
  }

  for (const entry of listDirectoryEntries(absoluteDir)) {
    if (entry.name === 'index.md' || EXCLUDED_MARKDOWN_FILES.has(entry.name)) {
      continue
    }

    const relativePath = path.join(relativeDir, entry.name)

    if (entry.isDirectory()) {
      const group = buildDirectoryGroup(docsRoot, relativePath)
      if (group.items.length > 0) {
        items.push(group)
      }
      continue
    }

    if (isMarkdownFile(entry.name)) {
      items.push({
        text: titleForMarkdownFile(path.join(absoluteDir, entry.name)),
        link: linkForMarkdownPath(relativeDir, entry.name)
      })
    }
  }

  return {
    text: labelForDirectory(relativeDir),
    items
  }
}

function collectLinks(item, links) {
  if (item.link) {
    links.push(item.link)
  }

  for (const child of item.items ?? []) {
    collectLinks(child, links)
  }
}

function collectMarkdownLinks(docsRoot, relativeDir, links) {
  const absoluteDir = path.join(docsRoot, relativeDir)

  for (const entry of listDirectoryEntries(absoluteDir)) {
    const relativePath = path.join(relativeDir, entry.name)

    if (entry.isDirectory()) {
      collectMarkdownLinks(docsRoot, relativePath, links)
      continue
    }

    if (isSidebarMarkdownFile(entry.name)) {
      links.push(linkForMarkdownPath(relativeDir, entry.name))
    }
  }
}

function isTopLevelContentDirectory(name) {
  return !EXCLUDED_TOP_LEVEL.has(name) && !name.startsWith('.')
}

function listDirectories(dir) {
  return listDirectoryEntries(dir).filter((entry) => entry.isDirectory())
}

function listDirectoryEntries(dir) {
  return fs
    .readdirSync(dir, { withFileTypes: true })
    .filter((entry) => !entry.name.startsWith('.'))
    .sort(compareDirectoryEntries)
}

function compareDirectoryEntries(left, right) {
  if (left.isDirectory() !== right.isDirectory()) {
    return left.isDirectory() ? -1 : 1
  }

  return collator.compare(left.name, right.name)
}

function compareTopLevel(left, right) {
  const leftIndex = TOP_LEVEL_ORDER.indexOf(left)
  const rightIndex = TOP_LEVEL_ORDER.indexOf(right)

  if (leftIndex !== -1 || rightIndex !== -1) {
    if (leftIndex === -1) {
      return 1
    }
    if (rightIndex === -1) {
      return -1
    }
    return leftIndex - rightIndex
  }

  return collator.compare(left, right)
}

function compareLinks(left, right) {
  return collator.compare(left, right)
}

function labelForDirectory(relativeDir) {
  const parts = relativeDir.split(path.sep)
  const name = parts.at(-1)

  if (parts.length === 1 && TOP_LEVEL_LABELS.has(name)) {
    return TOP_LEVEL_LABELS.get(name)
  }

  return DIRECTORY_LABELS.get(name) ?? prettifyName(name)
}

function titleForMarkdownFile(filePath) {
  const text = fs.readFileSync(filePath, 'utf-8')
  const heading = text.match(/^#\s+(.+)$/m)?.[1]?.trim()

  return heading ? stripMarkdownInlineSyntax(heading) : prettifyName(path.basename(filePath, '.md'))
}

function stripMarkdownInlineSyntax(text) {
  return text
    .replace(/`([^`]+)`/g, '$1')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .replace(/[*_]/g, '')
    .trim()
}

function prettifyName(name) {
  return name
    .replace(/[-_]+/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase())
}

function linkForMarkdownPath(relativeDir, fileName) {
  const routeParts = relativeDir.split(path.sep).filter(Boolean)

  if (fileName === 'index.md') {
    return `/${routeParts.join('/')}/`
  }

  return `/${[...routeParts, path.basename(fileName, '.md')].join('/')}`
}

function isSidebarMarkdownFile(name) {
  return isMarkdownFile(name) && !EXCLUDED_MARKDOWN_FILES.has(name)
}

function isMarkdownFile(name) {
  return name.endsWith('.md')
}
